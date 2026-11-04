// SPDX-License-Identifier: AGPL-3.0-or-later

const HEADER_SIZE = 64;
const LEMMA_ENTRY_SIZE = 24;
const BLOCK_ENTRY_SIZE = 16;
const RECORD_ENTRY_SIZE = 24;
const LINE_CAPACITY = 8192;
const encoder = new TextEncoder();
const recordKinds = new Map([
    [
        ":no:",
        1
    ],
    [
        ":aj:",
        2
    ],
    [
        ":vs:",
        3
    ],
    [
        ":wd:",
        4
    ],
    [
        ":vb:",
        5
    ]
]);
function canonicalLemma(source) {
    const first = source.trim().split(/[ \t\r\n]/, 1)[0];
    const content = first.startsWith("!") ? first.slice(1) : first;
    return content.replaceAll(/[-_^+]/g, "");
}
function sameBlock(left, right) {
    return left.lemma === right.lemma && left.records.length === right.records.length && left.records.every((record, index)=>{
        const other = right.records[index];
        return record.kind === other.kind && record.stem === other.stem && record.keys === other.keys;
    });
}
function parseSources(sources) {
    const blocks = [];
    let ordinal = 0;
    for (const source of sources){
        let block;
        for (const originalLine of source.split("\n")){
            if (encoder.encode(originalLine).length >= LINE_CAPACITY - 1) {
                throw new Error("generation source line is too long");
            }
            const line = originalLine.trim();
            if (line === "" || line.startsWith("#") || line.startsWith("?")) continue;
            if (line.startsWith(":le:")) {
                const lemma = canonicalLemma(line.slice(4).trim());
                if (lemma === "") throw new Error("invalid generation lemma");
                block = {
                    lemma,
                    ordinal: ordinal++,
                    records: []
                };
                blocks.push(block);
                continue;
            }
            if (line.startsWith(":de:") || line.startsWith(";") || line.startsWith("@")) {
                throw new Error("unexpanded generation record");
            }
            const kind = recordKinds.get(line.slice(0, 4));
            if (kind === undefined) continue;
            if (block === undefined) {
                throw new Error("generation record appears before a lemma");
            }
            const separator = line.slice(4).search(/[ \t\r\n]/);
            if (separator <= 0) throw new Error("incomplete generation record");
            const stem = line.slice(4, separator + 4);
            const keys = line.slice(separator + 4).trim();
            if (keys === "") throw new Error("incomplete generation record");
            block.records.push({
                kind,
                stem,
                keys
            });
        }
    }
    const sorted = blocks.filter((block)=>block.records.length !== 0).sort((left, right)=>left.lemma < right.lemma ? -1 : left.lemma > right.lemma ? 1 : left.ordinal - right.ordinal);
    return sorted.filter((block, index)=>{
        for(let previous = index - 1; previous >= 0; previous--){
            if (sorted[previous].lemma !== block.lemma) break;
            if (sameBlock(sorted[previous], block)) return false;
        }
        return true;
    });
}
function putU32(view, offset, value) {
    view.setUint32(offset, value, true);
}
function putU64(view, offset, value) {
    view.setBigUint64(offset, value, true);
}
function payloadHash(payload) {
    let hash = 14695981039346656037n;
    for (const byte of payload){
        hash = BigInt.asUintN(64, (hash ^ BigInt(byte)) * 1099511628211n);
    }
    return hash;
}
function encodedSize(value) {
    return encoder.encode(value).length + 1;
}
function writeString(output, offset, value) {
    const bytes = encoder.encode(value);
    output.set(bytes, offset);
    output[offset + bytes.length] = 0;
    return offset + bytes.length + 1;
}
export function buildGenerIndex(sources) {
    const blocks = parseSources(sources);
    let lemmaCount = 0, recordCount = 0, stringSize = 0;
    for(let index = 0; index < blocks.length; index++){
        const block = blocks[index];
        if (index === 0 || blocks[index - 1].lemma !== block.lemma) {
            lemmaCount++;
            stringSize += encodedSize(block.lemma);
        }
        recordCount += block.records.length;
        for (const record of block.records){
            stringSize += encodedSize(record.stem) + encodedSize(record.keys);
        }
    }
    if (lemmaCount > 0xffff_ffff || blocks.length > 0xffff_ffff || recordCount > Number.MAX_SAFE_INTEGER) {
        throw new RangeError("generation index exceeds JavaScript limits");
    }
    const payloadSize = lemmaCount * LEMMA_ENTRY_SIZE + blocks.length * BLOCK_ENTRY_SIZE + recordCount * RECORD_ENTRY_SIZE + stringSize;
    if (!Number.isSafeInteger(payloadSize)) {
        throw new RangeError("generation index exceeds JavaScript limits");
    }
    const payload = new Uint8Array(payloadSize);
    const view = new DataView(payload.buffer);
    let lemmaCursor = 0;
    let blockCursor = lemmaCount * LEMMA_ENTRY_SIZE;
    let recordCursor = blockCursor + blocks.length * BLOCK_ENTRY_SIZE;
    const stringBase = recordCursor + recordCount * RECORD_ENTRY_SIZE;
    let stringCursor = stringBase;
    let firstRecord = 0n;
    for(let start = 0; start < blocks.length;){
        let end = start + 1;
        while(end < blocks.length && blocks[end].lemma === blocks[start].lemma){
            end++;
        }
        const keyOffset = stringCursor - stringBase;
        stringCursor = writeString(payload, stringCursor, blocks[start].lemma);
        putU64(view, lemmaCursor, BigInt(keyOffset));
        putU64(view, lemmaCursor + 8, BigInt((blockCursor - lemmaCount * LEMMA_ENTRY_SIZE) / BLOCK_ENTRY_SIZE));
        putU32(view, lemmaCursor + 16, end - start);
        lemmaCursor += LEMMA_ENTRY_SIZE;
        for(let current = start; current < end; current++){
            const block = blocks[current];
            putU64(view, blockCursor, firstRecord);
            putU32(view, blockCursor + 8, block.records.length);
            blockCursor += BLOCK_ENTRY_SIZE;
            for (const record of block.records){
                const stemOffset = stringCursor - stringBase;
                stringCursor = writeString(payload, stringCursor, record.stem);
                const keysOffset = stringCursor - stringBase;
                stringCursor = writeString(payload, stringCursor, record.keys);
                putU32(view, recordCursor, record.kind);
                putU64(view, recordCursor + 8, BigInt(stemOffset));
                putU64(view, recordCursor + 16, BigInt(keysOffset));
                recordCursor += RECORD_ENTRY_SIZE;
                firstRecord++;
            }
        }
        start = end;
    }
    const header = new Uint8Array(HEADER_SIZE);
    header.set(encoder.encode("MORPHGEN"));
    const headerView = new DataView(header.buffer);
    putU32(headerView, 8, 1);
    putU32(headerView, 12, 1);
    putU64(headerView, 16, BigInt(lemmaCount));
    putU64(headerView, 24, BigInt(blocks.length));
    putU64(headerView, 32, BigInt(recordCount));
    putU64(headerView, 40, BigInt(stringSize));
    putU64(headerView, 48, payloadHash(payload));
    const result = new Uint8Array(HEADER_SIZE + payload.length);
    result.set(header);
    result.set(payload, HEADER_SIZE);
    return result;
}
