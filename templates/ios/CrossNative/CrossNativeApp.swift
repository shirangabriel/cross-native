import SwiftUI

@main
struct CrossNativeApp: App {
    var body: some Scene {
        WindowGroup {
            ZStack {
                Color(uiColor: .systemBackground).ignoresSafeArea()
                Text("Hello World")
                    .font(.title3)
                    .foregroundStyle(.primary)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }
}
