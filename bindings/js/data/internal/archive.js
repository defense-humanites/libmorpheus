// SPDX-License-Identifier: AGPL-3.0-or-later

const TAR_BLOCK_SIZE = 512;
const decoder = new TextDecoder();

function decodeString(bytes) {
  const zero = bytes.indexOf(0);
  return decoder.decode(zero === -1 ? bytes : bytes.subarray(0, zero));
}

function parseNumber(bytes, field) {
  if ((bytes[0] & 0x80) !== 0) {
    let value = BigInt(bytes[0] & 0x7f);
    for (const byte of bytes.subarray(1)) value = (value << 8n) | BigInt(byte);
    if (value > BigInt(Number.MAX_SAFE_INTEGER)) {
      throw new Error(`tar ${field} exceeds JavaScript limits`);
    }
    return Number(value);
  }
  const source = decodeString(bytes).trim();
  if (source === "") return 0;
  if (!/^[0-7]+$/.test(source)) throw new Error(`invalid tar ${field}`);
  const value = Number.parseInt(source, 8);
  if (!Number.isSafeInteger(value)) throw new Error(`invalid tar ${field}`);
  return value;
}

function verifyChecksum(header) {
  const expected = parseNumber(header.subarray(148, 156), "checksum");
  let actual = 0;
  for (let index = 0; index < header.length; index++) {
    actual += index >= 148 && index < 156 ? 0x20 : header[index];
  }
  if (actual !== expected) throw new Error("tar header checksum mismatch");
}

function parsePax(content) {
  const fields = new Map();
  let offset = 0;
  while (offset < content.length) {
    const space = content.indexOf(0x20, offset);
    if (space === -1) throw new Error("invalid PAX record length");
    const lengthText = decoder.decode(content.subarray(offset, space));
    if (!/^[1-9][0-9]*$/.test(lengthText)) {
      throw new Error("invalid PAX record length");
    }
    const length = Number.parseInt(lengthText, 10);
    const end = offset + length;
    if (!Number.isSafeInteger(length) || end > content.length || content[end - 1] !== 0x0a) {
      throw new Error("truncated PAX record");
    }
    const record = decoder.decode(content.subarray(space + 1, end - 1));
    const equals = record.indexOf("=");
    if (equals <= 0) throw new Error("invalid PAX record");
    fields.set(record.slice(0, equals), record.slice(equals + 1));
    offset = end;
  }
  return fields;
}

export function parseTarArchive(archive) {
  const entries = [];
  let offset = 0;
  let nextPax = new Map();
  let globalPax = new Map();
  let longPath;
  let longLinkPath;
  let zeroBlocks = 0;

  while (offset + TAR_BLOCK_SIZE <= archive.length) {
    const header = archive.subarray(offset, offset + TAR_BLOCK_SIZE);
    offset += TAR_BLOCK_SIZE;
    if (header.every((byte) => byte === 0)) {
      if (++zeroBlocks === 2) return entries;
      continue;
    }
    zeroBlocks = 0;
    verifyChecksum(header);
    const size = parseNumber(header.subarray(124, 136), "size");
    const paddedSize = Math.ceil(size / TAR_BLOCK_SIZE) * TAR_BLOCK_SIZE;
    if (offset + paddedSize > archive.length) throw new Error("truncated tar entry");
    const content = archive.subarray(offset, offset + size);
    offset += paddedSize;
    const type = String.fromCharCode(header[156] || 0x30);
    const mode = parseNumber(header.subarray(100, 108), "mode");
    const name = decodeString(header.subarray(0, 100));
    const prefix = decodeString(header.subarray(345, 500));
    const headerPath = prefix === "" ? name : `${prefix}/${name}`;

    if (type === "x") {
      nextPax = parsePax(content);
      continue;
    }
    if (type === "g") {
      globalPax = new Map([...globalPax, ...parsePax(content)]);
      continue;
    }
    if (type === "L") {
      longPath = decodeString(content);
      continue;
    }
    if (type === "K") {
      longLinkPath = decodeString(content);
      continue;
    }
    const path = nextPax.get("path") ?? globalPax.get("path") ?? longPath ?? headerPath;
    const linkPath = nextPax.get("linkpath") ?? globalPax.get("linkpath") ??
      longLinkPath ?? decodeString(header.subarray(157, 257));
    nextPax = new Map();
    longPath = undefined;
    longLinkPath = undefined;
    entries.push({ path, type, content, mode, linkPath });
  }
  throw new Error("tar archive has no complete end marker");
}
