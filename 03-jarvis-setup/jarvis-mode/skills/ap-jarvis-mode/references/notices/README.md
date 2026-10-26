# Dependency and artwork notices

The package includes the original generated JARVIS artwork, with neutral filenames and member-configured labels. No private reference screenshot, personal records, application state, credentials, or preconfigured device identity is included.

Hermes and the optional Talk integration retain their upstream notices in `payload/host/licenses/`. Those notices are legal attribution, not a bundled user identity. The host source is obtained from its official public repository; the six optional compatibility patches are included separately.

The optional computer-control application, used only by the optional hands extra on a Mac main device, is obtained from the vendor's official pinned release. Its binary is not bundled here. See `payload/hands/cua-driver-notice.txt` and `CuaDriver-MIT.txt`. The member's agent verifies the download hash and signature before installation. Native permissions are granted on the member's own main device.

Artwork hashes are listed in `art-provenance.json`. The package manifest hashes every distributed file; the external archive checksum verifies the downloaded archive itself.
