//
//  BundledPeerRequirement.swift
//  Shared
//

import Foundation
import Security
import XPC

/// Pins XPC peers to the signed binaries shipped in the same application bundle.
/// Ad-hoc signatures have no Apple team identifier, so a same-team check rejects them.
@available(macOS 26.0, *)
enum BundledPeerRequirement {
    static func make(bundleURL: URL, identifier: String) throws -> XPCPeerRequirement {
        let hashes = xpc_array_create_empty()
        for architecture in ["arm64", "x86_64"] {
            var code: SecStaticCode?
            let attributes = [kSecCodeAttributeArchitecture: architecture] as CFDictionary
            let status = SecStaticCodeCreateWithPathAndAttributes(
                bundleURL.standardizedFileURL as CFURL, [], attributes, &code
            )
            // A development build may contain only one architecture.
            if status != errSecSuccess { continue }
            guard status == errSecSuccess, let code else {
                throw NSError(domain: NSOSStatusErrorDomain, code: Int(status))
            }
            let validation = SecStaticCodeCheckValidity(code, SecCSFlags(rawValue: kSecCSCheckAllArchitectures), nil)
            guard validation == errSecSuccess else {
                throw NSError(domain: NSOSStatusErrorDomain, code: Int(validation))
            }
            var information: CFDictionary?
            let copyStatus = SecCodeCopySigningInformation(code, SecCSFlags(rawValue: kSecCSSigningInformation), &information)
            guard copyStatus == errSecSuccess,
                  let info = information as? [String: Any],
                  info[kSecCodeInfoIdentifier as String] as? String == identifier,
                  let cdHashes = info[kSecCodeInfoCdHashes as String] as? [Data],
                  !cdHashes.isEmpty else {
                throw NSError(domain: NSOSStatusErrorDomain, code: Int(errSecCSReqFailed))
            }
            for hash in cdHashes {
                hash.withUnsafeBytes { bytes in
                    let value = xpc_data_create(bytes.baseAddress, bytes.count)
                    xpc_array_append_value(hashes, value)
                }
            }
        }
        guard xpc_array_get_count(hashes) > 0 else {
            throw NSError(domain: NSOSStatusErrorDomain, code: Int(errSecCSUnsigned))
        }
        let allowedHashes = xpc_dictionary_create_empty()
        xpc_dictionary_set_value(allowedHashes, "$in", hashes)
        let requirement = xpc_dictionary_create_empty()
        xpc_dictionary_set_string(requirement, "signing-identifier", identifier)
        xpc_dictionary_set_value(requirement, "cdhash", allowedHashes)
        return XPCPeerRequirement(lightweightCodeRequirements: XPCDictionary(requirement))
    }
}
