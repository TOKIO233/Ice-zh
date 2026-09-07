//
//  main.swift
//  Ice
//

import SwiftUI

// Run the real XPC handshake before starting any UI or permission requests.
if CommandLine.arguments.contains("--xpc-smoke-test") {
    if #available(macOS 26.0, *) {
        let connected = MenuBarItemService.Connection.shared.checkConnection()
        print(connected ? "XPC_HANDSHAKE_OK" : "XPC_HANDSHAKE_FAILED")
        exit(connected ? 0 : 1)
    }
    print("XPC_SMOKE_TEST_REQUIRES_MACOS_26")
    exit(77)
}

IceApp.main()
