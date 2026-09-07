//
//  BoundedCaptureQueue.swift
//  Ice
//

import Foundation
import os.lock

/// Limits waiting for a system capture that may never return, with at most one
/// operation in flight. A timeout keeps the slot occupied until the work ends.
final class BoundedCaptureQueue: Sendable {
    private let queue = DispatchQueue(label: "ScreenCapture.captureQueue", qos: .userInitiated)
    private let busy = OSAllocatedUnfairLock(initialState: false)

    func perform<Value: Sendable>(
        timeout: DispatchTimeInterval,
        operation: @escaping @Sendable () -> Value?
    ) -> Value? {
        guard busy.withLock({ occupied in
            guard !occupied else { return false }
            occupied = true
            return true
        }) else { return nil }

        let result = OSAllocatedUnfairLock<Value?>(initialState: nil)
        let completion = DispatchSemaphore(value: 0)
        queue.async { [busy] in
            let value = operation()
            result.withLock { $0 = value }
            busy.withLock { $0 = false }
            completion.signal()
        }
        guard completion.wait(timeout: .now() + timeout) == .success else {
            return nil
        }
        return result.withLock { $0 }
    }
}
