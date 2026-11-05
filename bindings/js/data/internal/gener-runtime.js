// SPDX-License-Identifier: AGPL-3.0-or-later

import createGenerPreparer from "./gener-preparer.mjs";
import process from "node:process";
import { buildGenerIndex } from "./gener-index.js";
import { GENER_CORPUS_EXCEPTIONS, GENER_CORPUS_FILES, GENER_INDEX_SHA256, GENER_PREPARED_SHA256 } from "./gener-manifest.js";
function parentPath(path) {
    const separator = path.lastIndexOf("/");
    return separator <= 0 ? "/" : path.slice(0, separator);
}
function populateSupportStemlib(fileSystem, files) {
    fileSystem.mkdirTree("/morphlib/Greek");
    for (const [path, content] of files){
        if (!path.startsWith("Greek/")) continue;
        const destination = `/morphlib/${path}`;
        fileSystem.mkdirTree(parentPath(destination));
        fileSystem.writeFile(destination, content);
    }
}
export async function prepareGenerIndex(alpheiosFiles, perseidsFiles, digest) {
    const errors = [];
    const module = await createGenerPreparer({
        noInitialRun: true,
        print: ()=>undefined,
        printErr: (message)=>errors.push(String(message))
    });
    const fileSystem = module.FS;
    populateSupportStemlib(fileSystem, perseidsFiles);
    fileSystem.mkdirTree("/input");
    const inputs = [];
    for (const relative of GENER_CORPUS_FILES){
        const content = alpheiosFiles.get(`Greek/${relative}`);
        if (content === undefined) {
            throw new Error(`Alpheios generation source is missing: ${relative}`);
        }
        const input = `/input/${relative}`;
        fileSystem.mkdirTree(parentPath(input));
        fileSystem.writeFile(input, content);
        inputs.push(input);
    }
    fileSystem.writeFile("/exceptions.tsv", GENER_CORPUS_EXCEPTIONS);
    const previousExitCode = process.exitCode;
    let status;
    try {
        status = module.callMain([
            "--exceptions",
            "/exceptions.tsv",
            "/prepared.txt",
            ...inputs
        ]);
    } finally{
        process.exitCode = previousExitCode;
    }
    if (status !== 0) {
        const detail = errors.slice(-8).join("\n");
        throw new Error(`experimental generation source preparation failed (${status})` + (detail === "" ? "" : `:\n${detail}`));
    }
    const prepared = fileSystem.readFile("/prepared.txt");
    if (await digest(prepared) !== GENER_PREPARED_SHA256) {
        throw new Error("experimental generation source digest mismatch");
    }
    const source = new TextDecoder("utf-8", {
        fatal: true
    }).decode(prepared);
    const index = buildGenerIndex([
        source
    ]);
    if (await digest(index) !== GENER_INDEX_SHA256) {
        throw new Error("experimental generation index digest mismatch");
    }
    return index;
}
