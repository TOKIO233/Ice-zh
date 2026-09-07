import Foundation

@main
struct CaptureQueueTests {
    static func main() {
        let queue = BoundedCaptureQueue()
        let release = DispatchSemaphore(value: 0)
        let entered = DispatchSemaphore(value: 0)
        let start = Date()
        let timedOut: Int? = queue.perform(timeout: .milliseconds(25)) {
            entered.signal()
            release.wait()
            return 42
        }
        precondition(timedOut == nil && Date().timeIntervalSince(start) < 0.5)
        precondition(entered.wait(timeout: .now() + 1) == .success)
        for _ in 0..<100 {
            let dropped: Int? = queue.perform(timeout: .milliseconds(25)) {
                preconditionFailure("A stalled capture must not accumulate more work")
            }
            precondition(dropped == nil)
        }
        release.signal()
        var recovered: Int?
        for _ in 0..<100 where recovered == nil {
            Thread.sleep(forTimeInterval: 0.005)
            recovered = queue.perform(timeout: .milliseconds(100)) { 7 }
        }
        precondition(recovered == 7, "Queue must recover after a late completion")
        let empty: Int? = queue.perform(timeout: .milliseconds(100)) { nil }
        precondition(empty == nil)
        let next: Int? = queue.perform(timeout: .milliseconds(100)) { 9 }
        precondition(next == 9)
        print("CAPTURE_QUEUE_TESTS_OK: timeout, backpressure, late completion, recovery, nil result")
    }
}
