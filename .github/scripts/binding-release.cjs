// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Create or complete the GitHub release of a binding tag (node-v*, python-v*)
// from staged assets, with the tag as title and docs/release-notes/<tag>.md
// as body. Idempotent: an existing release keeps its assets, gains missing
// ones, and a draft is published only once every expected asset is present.
// Binding releases never become the repository's "latest" release, which
// stays the native one.
//
// Called from actions/github-script:
//   const publish = require('./.github/scripts/binding-release.cjs')
//   await publish({ github, context, core, tag, sha, assetDirectory })

const fs = require('fs')
const path = require('path')

module.exports = async function publishBindingRelease({
  github,
  context,
  core,
  tag,
  sha,
  assetDirectory,
}) {
  const owner = context.repo.owner
  const repo = context.repo.repo
  const body = fs.readFileSync(`docs/release-notes/${tag}.md`, 'utf8')
  const expected = fs.readdirSync(assetDirectory).sort()
  if (!expected.includes('SHA256SUMS') || expected.length < 2) {
    throw new Error(`Incomplete asset set for ${tag}: ${expected.join(', ')}`)
  }

  let release
  try {
    release = (await github.rest.repos.getReleaseByTag({ owner, repo, tag })).data
  } catch (error) {
    if (error.status !== 404) throw error
  }
  if (release === undefined) {
    release = (await github.rest.repos.createRelease({
      owner,
      repo,
      // The tag exists: GitHub ignores target_commitish for an existing tag,
      // and `sha` only documents which commit the release describes.
      tag_name: tag,
      name: tag,
      body,
      draft: true,
      prerelease: false,
    })).data
  }

  const uploaded = new Set(release.assets.map((asset) => asset.name))
  for (const name of expected.filter((name) => !uploaded.has(name))) {
    if (!release.draft) {
      throw new Error(`Published release ${release.html_url} lacks ${name}`)
    }
    const data = fs.readFileSync(path.join(assetDirectory, name))
    await github.rest.repos.uploadReleaseAsset({
      owner,
      repo,
      release_id: release.id,
      name,
      data,
      headers: {
        'content-type': 'application/octet-stream',
        'content-length': data.length,
      },
    })
  }

  const updated = await github.rest.repos.updateRelease({
    owner,
    repo,
    release_id: release.id,
    name: tag,
    body,
    draft: false,
    prerelease: false,
    make_latest: 'false',
  })
  core.info(`Binding release: ${updated.data.html_url}`)
}
