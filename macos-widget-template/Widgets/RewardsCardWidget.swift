import SwiftUI
import WidgetKit

private let appGroupId = "group.com.cai.logi-battery-widget"
private let snapshotFileName = "battery_snapshot.json"
private let overrideKey = "deviceNameOverrides"

struct LogiBatteryWidget: Widget {
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: "LogiBatteryWidget", provider: Provider()) { entry in
            LogiBatteryEntryView(entry: entry)
        }
        .configurationDisplayName("Logi Battery")
        .description("Show battery levels for Logitech devices.")
        .supportedFamilies([.systemSmall, .systemMedium, .systemLarge])
    }
}

extension LogiBatteryWidget {
    struct Provider: TimelineProvider {
        typealias Entry = LogiBatteryWidget.Entry

        func placeholder(in context: Context) -> Entry {
            Entry(date: Date(), snapshot: .placeholder)
        }

        func getSnapshot(in context: Context, completion: @escaping (Entry) -> Void) {
            completion(Entry(date: Date(), snapshot: loadSnapshot() ?? .empty))
        }

        func getTimeline(in context: Context, completion: @escaping (Timeline<Entry>) -> Void) {
            let snapshot = loadSnapshot() ?? .empty
            let next = Date().addingTimeInterval(15 * 60)
            let entry = Entry(date: Date(), snapshot: snapshot)
            completion(Timeline(entries: [entry], policy: .after(next)))
        }
    }
}

extension LogiBatteryWidget {
    struct Entry: TimelineEntry {
        let date: Date
        let snapshot: BatterySnapshot
    }
}

struct BatteryDevice: Identifiable, Codable {
    var id: String { deviceId }
    let deviceId: String
    let deviceName: String
    let level: Int
    let updatedAt: TimeInterval?
}

struct BatterySnapshot: Codable {
    let devices: [BatteryDevice]
    let generatedAt: TimeInterval

    static let empty = BatterySnapshot(
        devices: [],
        generatedAt: Date().timeIntervalSince1970
    )

    static let placeholder = BatterySnapshot(
        devices: [
            BatteryDevice(deviceId: "mx-anywhere-3", deviceName: "Mx Anywhere 3", level: 88, updatedAt: Date().timeIntervalSince1970),
            BatteryDevice(deviceId: "mx-keys-mini", deviceName: "Mx Keys Mini", level: 76, updatedAt: Date().timeIntervalSince1970)
        ],
        generatedAt: Date().timeIntervalSince1970
    )
}

struct LogiBatteryEntryView: View {
    let entry: LogiBatteryWidget.Entry

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("Logi Battery")
                    .font(.headline)
                Spacer()
                Text(formatDate(entry.snapshot.generatedAt))
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }

            if entry.snapshot.devices.isEmpty {
                Text("No data yet")
                    .foregroundColor(.secondary)
            } else {
                ForEach(entry.snapshot.devices.prefix(4)) { device in
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Image(systemName: deviceIconName(for: device))
                                .foregroundColor(.secondary)
                            Text(device.deviceName)
                                .font(.subheadline)
                                .lineLimit(1)
                            Spacer()
                            Text("\(device.level)%")
                                .font(.subheadline)
                                .bold()
                                .foregroundColor(batteryColor(device.level))
                        }
                        BatteryBar(level: device.level)
                        Text("Updated: \(formatDate(device.updatedAt))")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }
            }
            Spacer()
        }
        .padding(12)
        .containerBackground(.background, for: .widget)
    }
}

struct BatteryBar: View {
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
    formatter.dateFormat = "MM-dd HH:mm"
    return formatter.string(from: date)
}

private func deviceIconName(for device: BatteryDevice) -> String {
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

private func loadSnapshot() -> BatterySnapshot? {
    guard let containerURL = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroupId) else {
        return nil
    }
    let fileURL = containerURL.appendingPathComponent(snapshotFileName)
    guard let data = try? Data(contentsOf: fileURL) else { return nil }
    guard let snapshot = try? JSONDecoder().decode(BatterySnapshot.self, from: data) else { return nil }
    let overrides = loadOverrides()
    if overrides.isEmpty { return snapshot }
    let updatedDevices = snapshot.devices.map { device in
        let name = overrides[device.deviceId]?.trimmingCharacters(in: .whitespacesAndNewlines)
        if let name, !name.isEmpty {
            return BatteryDevice(deviceId: device.deviceId, deviceName: name, level: device.level, updatedAt: device.updatedAt)
        }
        return device
    }
    return BatterySnapshot(devices: updatedDevices, generatedAt: snapshot.generatedAt)
}

private func loadOverrides() -> [String: String] {
    guard let defaults = UserDefaults(suiteName: appGroupId) else { return [:] }
    return defaults.dictionary(forKey: overrideKey) as? [String: String] ?? [:]
}
