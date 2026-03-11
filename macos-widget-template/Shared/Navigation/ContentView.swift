import SwiftUI

#if os(macOS) && !APP_EXTENSION
import AppKit
import ServiceManagement
import SQLite3
import WidgetKit

private let appGroupId = "group.com.cai.logi-battery-widget"
private let snapshotFileName = "battery_snapshot.json"
private let refreshInterval: TimeInterval = 600
private let overrideKey = "deviceNameOverrides"

struct AppBatteryDevice: Identifiable, Codable {
    var id: String { deviceId }
    let deviceId: String
    let deviceName: String
    let level: Int
    let updatedAt: TimeInterval?
}

struct AppBatterySnapshot: Codable {
    let devices: [AppBatteryDevice]
    let generatedAt: TimeInterval
}

final class BatteryStore: ObservableObject {
    @Published var snapshot: AppBatterySnapshot?
    @Published var lastError: String?
    @Published var isRefreshing = false
    @Published var nameOverrides: [String: String]
    @Published var launchAtLoginEnabled: Bool

    private let timer = Timer.publish(every: refreshInterval, on: .main, in: .common).autoconnect()

    init() {
        nameOverrides = loadOverrides()
        #if !APP_EXTENSION
        if #available(macOS 13.0, *) {
            launchAtLoginEnabled = (SMAppService.mainApp.status == .enabled)
        } else {
            launchAtLoginEnabled = false
        }
        #else
        launchAtLoginEnabled = false
        #endif
    }

    func startTimer() {
        _ = timer
    }

    func refresh() {
        guard !isRefreshing else { return }
        isRefreshing = true
        DispatchQueue.global(qos: .userInitiated).async {
            let result = loadSnapshotFromLogiOptions(overrides: self.nameOverrides)
            DispatchQueue.main.async {
                self.isRefreshing = false
                switch result {
                case .success(let snapshot):
                    self.snapshot = snapshot
                    self.lastError = nil
                    saveSnapshot(snapshot)
                    WidgetCenter.shared.reloadAllTimelines()
                case .failure(let error):
                    self.lastError = error.localizedDescription
                }
            }
        }
    }

    func saveOverrides(_ overrides: [String: String]) {
        nameOverrides = overrides
        persistOverrides(overrides)
        refresh()
    }

    func setLaunchAtLogin(_ enabled: Bool) {
        #if !APP_EXTENSION
        guard #available(macOS 13.0, *) else {
            lastError = "Launch at login requires macOS 13 or newer."
            launchAtLoginEnabled = false
            return
        }
        do {
            if enabled {
                try SMAppService.mainApp.register()
            } else {
                try SMAppService.mainApp.unregister()
            }
            launchAtLoginEnabled = enabled
        } catch {
            lastError = error.localizedDescription
        }
        #else
        lastError = "Launch at login is not available in extensions."
        launchAtLoginEnabled = false
        #endif
    }
}

struct ContentView: View {
    @ObservedObject var store: BatteryStore
    @State private var showNameEditor = false
    @State private var edits: [String: String] = [:]

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Logi Battery Widget")
                    .font(.title2)
                    .bold()
                Spacer()
                Button(action: store.refresh) {
                    if store.isRefreshing {
                        ProgressView()
                            .controlSize(.small)
                    } else {
                        Text("Refresh")
                    }
                }
                .disabled(store.isRefreshing)
            }

            if let error = store.lastError {
                Text(error)
                    .foregroundColor(.red)
                    .font(.caption)
            }

            if let snapshot = store.snapshot, !snapshot.devices.isEmpty {
                List(snapshot.devices) { device in
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Image(systemName: deviceIconName(for: device))
                                .foregroundColor(.secondary)
                            Text(device.deviceName)
                                .font(.headline)
                            Spacer()
                            Text("\(device.level)%")
                                .font(.headline)
                                .foregroundColor(batteryColor(device.level))
                        }
                        AppBatteryBar(level: device.level)
                        Text("Updated: \(formatDate(device.updatedAt))")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding(.vertical, 4)
                }
                .frame(minHeight: 260)
            } else {
                Text("No devices found. Make sure Logi Options+ is installed and running.")
                    .foregroundColor(.secondary)
            }

            HStack(spacing: 12) {
                Button("Edit Names") {
                    edits = store.nameOverrides
                    showNameEditor = true
                }
                #if !APP_EXTENSION
                Toggle("Launch at login", isOn: Binding(
                    get: { store.launchAtLoginEnabled },
                    set: { store.setLaunchAtLogin($0) }
                ))
                .toggleStyle(.switch)
                #endif
            }

            Spacer()
        }
        .padding(16)
        .onAppear {
            store.startTimer()
            store.refresh()
        }
        .onReceive(Timer.publish(every: refreshInterval, on: .main, in: .common).autoconnect()) { _ in
            store.refresh()
        }
        .sheet(isPresented: $showNameEditor) {
            DeviceNameEditor(snapshot: store.snapshot, edits: $edits) {
                store.saveOverrides(edits)
                showNameEditor = false
            } onCancel: {
                showNameEditor = false
            }
        }
    }
}

struct DeviceNameEditor: View {
    let snapshot: AppBatterySnapshot?
    @Binding var edits: [String: String]
    let onSave: () -> Void
    let onCancel: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Custom Device Names")
                .font(.headline)

            if let devices = snapshot?.devices, !devices.isEmpty {
                List(devices) { device in
                    HStack {
                        Text(device.deviceName)
                            .frame(width: 180, alignment: .leading)
                        TextField("Custom name", text: binding(for: device.deviceId))
                    }
                }
                .frame(minHeight: 240)
            } else {
                Text("No devices available yet. Refresh the app first.")
                    .foregroundColor(.secondary)
            }

            HStack {
                Spacer()
                Button("Cancel", action: onCancel)
                Button("Save") { onSave() }
                    .keyboardShortcut(.defaultAction)
            }
        }
        .padding(16)
        .frame(minWidth: 460, minHeight: 360)
    }

    private func binding(for deviceId: String) -> Binding<String> {
        Binding(
            get: { edits[deviceId, default: ""] },
            set: { edits[deviceId] = $0 }
        )
    }
}

struct AppBatteryBar: View {
    let level: Int

    var body: some View {
        GeometryReader { geo in
            let width = max(0, min(1, Double(level) / 100.0))
            ZStack(alignment: .leading) {
                Capsule()
                    .fill(Color.gray.opacity(0.2))
                    .frame(height: 6)
                Capsule()
                    .fill(batteryColor(level))
                    .frame(width: geo.size.width * width, height: 6)
            }
        }
        .frame(height: 6)
    }
}

private func batteryColor(_ level: Int) -> Color {
    switch level {
    case 0..<20:
        return .red
    case 20..<50:
        return .orange
    default:
        return .green
    }
}

private func formatDate(_ timestamp: TimeInterval?) -> String {
    guard let timestamp else { return "--" }
    let date = Date(timeIntervalSince1970: timestamp)
    let formatter = DateFormatter()
    formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
    return formatter.string(from: date)
}

private func loadSnapshotFromLogiOptions(overrides: [String: String]) -> Result<AppBatterySnapshot, Error> {
    let dbPath = (NSHomeDirectory() as NSString).appendingPathComponent("Library/Application Support/LogiOptionsPlus/settings.db")

    var db: OpaquePointer?
    guard sqlite3_open(dbPath, &db) == SQLITE_OK else {
        return .failure(NSError(domain: "LogiBattery", code: 1, userInfo: [NSLocalizedDescriptionKey: "Failed to open settings.db"]))
    }
    defer { sqlite3_close(db) }

    let query = "SELECT file FROM data LIMIT 1"
    var stmt: OpaquePointer?
    guard sqlite3_prepare_v2(db, query, -1, &stmt, nil) == SQLITE_OK else {
        return .failure(NSError(domain: "LogiBattery", code: 2, userInfo: [NSLocalizedDescriptionKey: "Failed to query settings.db"]))
    }
    defer { sqlite3_finalize(stmt) }

    guard sqlite3_step(stmt) == SQLITE_ROW else {
        return .failure(NSError(domain: "LogiBattery", code: 3, userInfo: [NSLocalizedDescriptionKey: "No data found in settings.db"]))
    }

    guard let cString = sqlite3_column_text(stmt, 0) else {
        return .failure(NSError(domain: "LogiBattery", code: 4, userInfo: [NSLocalizedDescriptionKey: "Invalid data row in settings.db"]))
    }

    let jsonString = String(cString: cString)
    guard let data = jsonString.data(using: .utf8) else {
        return .failure(NSError(domain: "LogiBattery", code: 5, userInfo: [NSLocalizedDescriptionKey: "Failed to decode JSON from settings.db"]))
    }

    let obj = try? JSONSerialization.jsonObject(with: data, options: [])
    guard let dict = obj as? [String: Any] else {
        return .failure(NSError(domain: "LogiBattery", code: 6, userInfo: [NSLocalizedDescriptionKey: "Unexpected JSON structure in settings.db"]))
    }

    var devices: [AppBatteryDevice] = []
    for (key, value) in dict {
        guard key.hasPrefix("battery/"), key.hasSuffix("/warning_notification"),
              let payload = value as? [String: Any] else {
            continue
        }
        guard let level = payload["batteryLevel"] as? Int else { continue }
        let time = parseTimestamp(payload["time"])
        let deviceId = key.components(separatedBy: "/")[1]
        let baseName = formatDeviceName(deviceId)
        let name = overrides[deviceId]?.trimmingCharacters(in: .whitespacesAndNewlines)
        let deviceName = (name?.isEmpty == false) ? name! : baseName
        devices.append(AppBatteryDevice(deviceId: deviceId, deviceName: deviceName, level: level, updatedAt: time))
    }

    devices.sort { $0.level < $1.level }
    return .success(AppBatterySnapshot(devices: devices, generatedAt: Date().timeIntervalSince1970))
}

private func parseTimestamp(_ value: Any?) -> TimeInterval? {
    if let intVal = value as? Int {
        return TimeInterval(intVal)
    }
    if let strVal = value as? String, let intVal = TimeInterval(strVal) {
        return intVal
    }
    if let doubleVal = value as? Double {
        return doubleVal
    }
    return nil
}

private func formatDeviceName(_ deviceId: String) -> String {
    var parts = deviceId.split(separator: "-").map { String($0) }
    if let last = parts.last, last.count == 5, last.allSatisfy({ $0.isHexDigit }) {
        parts.removeLast()
    }
    return parts.map { $0.capitalized }.joined(separator: " ")
}

private func deviceIconName(for device: AppBatteryDevice) -> String {
    let name = device.deviceName.lowercased()
    let id = device.deviceId.lowercased()
    if name.contains("key") || id.contains("key") || name.contains("keyboard") {
        return "keyboard"
    }
    if name.contains("mouse") || id.contains("mouse") || id.contains("anywhere") || id.contains("master") {
        return "computermouse"
    }
    return "bolt.batteryblock"
}

private func saveSnapshot(_ snapshot: AppBatterySnapshot) {
    guard let containerURL = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroupId) else {
        return
    }
    let fileURL = containerURL.appendingPathComponent(snapshotFileName)
    do {
        let data = try JSONEncoder().encode(snapshot)
        try data.write(to: fileURL, options: .atomic)
    } catch {
        print("Failed to save snapshot: \(error)")
    }
}

private func loadOverrides() -> [String: String] {
    guard let defaults = UserDefaults(suiteName: appGroupId) else { return [:] }
    return defaults.dictionary(forKey: overrideKey) as? [String: String] ?? [:]
}

private func persistOverrides(_ overrides: [String: String]) {
    guard let defaults = UserDefaults(suiteName: appGroupId) else { return }
    defaults.set(overrides, forKey: overrideKey)
}

struct MenuBarView: View {
    @ObservedObject var store: BatteryStore

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Logi Battery")
                .font(.headline)
            if let snapshot = store.snapshot, !snapshot.devices.isEmpty {
                ForEach(snapshot.devices.prefix(3)) { device in
                    HStack {
                        Image(systemName: deviceIconName(for: device))
                            .foregroundColor(.secondary)
                        Text(device.deviceName)
                            .font(.caption)
                            .lineLimit(1)
                        Spacer()
                        Text("\(device.level)%")
                            .font(.caption)
                            .foregroundColor(batteryColor(device.level))
                    }
                }
            } else {
                Text("No devices")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            Divider()
            Button("Refresh Now") { store.refresh() }
            Button("Open App") {
                NSApp.activate(ignoringOtherApps: true)
                NSApp.windows.first?.makeKeyAndOrderFront(nil)
            }
            Button("Quit") { NSApp.terminate(nil) }
        }
        .padding(8)
        .frame(width: 220)
    }
}

#else

struct ContentView: View {
    var body: some View {
        Text("macOS only")
    }
}

#endif
