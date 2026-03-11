import SwiftUI

@main
struct FrutaApp: App {
    #if os(macOS)
    @StateObject private var store = BatteryStore()
    #endif

    var body: some Scene {
        #if os(macOS)
        if #available(macOS 13.0, *) {
            MenuBarExtra("Logi Battery", systemImage: "bolt.batteryblock") {
                MenuBarView(store: store)
            }
        }
        WindowGroup {
            ContentView(store: store)
        }
        #else
        WindowGroup {
            ContentView()
        }
        #endif
    }
}
