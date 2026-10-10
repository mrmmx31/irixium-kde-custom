// SPDX-License-Identifier: GPL-3.0-or-later
// Read-only KColorScheme adapter. The GTK variable/state policy is documented
// by KDE kde-gtk-config v6.3.4, kded/configvalueprovider.cpp, SHA-256:
// fb3e403291fb667f2495e967772ec7b374bedef661793488c5adc51b55197eee.
// https://github.com/KDE/kde-gtk-config/blob/v6.3.4/kded/configvalueprovider.cpp
// No QGuiApplication, widgets, DBus, config writes or fixed final RGB values.
#include <KColorScheme>
#include <KConfigGroup>
#include <KSharedConfig>
#include <kcolorscheme_version.h>
#include <QColor>
#include <QCoreApplication>
#include <QCryptographicHash>
#include <QDir>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QPalette>
#include <cerrno>
#include <cstring>
#include <fcntl.h>
#include <stdexcept>
#include <sys/stat.h>
#include <unistd.h>

using KCS = KColorScheme;
static constexpr qint64 InputLimit = 2 * 1024 * 1024;

static QByteArray readInput(const QString &path)
{
    int fd = ::open(QFile::encodeName(path).constData(), O_RDONLY | O_NOFOLLOW | O_NONBLOCK);
    if (fd < 0) throw std::runtime_error(std::strerror(errno));
    struct stat info;
    if (::fstat(fd, &info) || !S_ISREG(info.st_mode) || info.st_size > InputLimit) {
        ::close(fd); throw std::runtime_error("Input must be a bounded regular file, without symlink");
    }
    QByteArray bytes;
    char buffer[8192];
    for (;;) {
        ssize_t count = ::read(fd, buffer, sizeof(buffer));
        if (count < 0 && errno == EINTR) continue;
        if (count < 0) { ::close(fd); throw std::runtime_error("Cannot read scheme input"); }
        if (!count) break;
        bytes.append(buffer, count);
        if (bytes.size() > InputLimit) { ::close(fd); throw std::runtime_error("Input grew beyond limit"); }
    }
    ::close(fd);
    return bytes;
}

static QString digest(const QByteArray &bytes)
{
    return QString::fromLatin1(QCryptographicHash::hash(bytes, QCryptographicHash::Sha256).toHex());
}

struct Family {
    KCS::ColorSet set;
    const char *background[4];
    const char *foreground[4];
};
static const Family families[] = {
    {KCS::Window,
     {"theme_bg_color_breeze", "theme_unfocused_bg_color_breeze", "insensitive_bg_color_breeze", "insensitive_unfocused_bg_color_breeze"},
     {"theme_fg_color_breeze", "theme_unfocused_fg_color_breeze", "insensitive_fg_color_breeze", "insensitive_unfocused_fg_color_breeze"}},
    {KCS::Button,
     {"theme_button_background_normal_breeze", "theme_button_background_backdrop_breeze", "theme_button_background_insensitive_breeze", "theme_button_background_backdrop_insensitive_breeze"},
     {"theme_button_foreground_normal_breeze", "theme_button_foreground_backdrop_breeze", "theme_button_foreground_insensitive_breeze", "theme_button_foreground_backdrop_insensitive_breeze"}},
    {KCS::View,
     {"theme_base_color_breeze", "theme_unfocused_base_color_breeze", "insensitive_base_color_breeze", "theme_unfocused_view_bg_color_breeze"},
     {"theme_text_color_breeze", "theme_unfocused_text_color_breeze", "insensitive_base_fg_color_breeze", "theme_unfocused_view_text_color_breeze"}},
    {KCS::Selection,
     {"theme_selected_bg_color_breeze", "theme_unfocused_selected_bg_color_breeze", "insensitive_selected_bg_color_breeze", "insensitive_unfocused_selected_bg_color_breeze"},
     {"theme_selected_fg_color_breeze", "theme_unfocused_selected_fg_color_breeze", "insensitive_selected_fg_color_breeze", "insensitive_unfocused_selected_fg_color_breeze"}},
};
static const Family header = {KCS::Header,
    {"theme_header_background_breeze", "theme_header_background_backdrop_breeze", "theme_header_background_backdrop_breeze", "theme_header_background_backdrop_breeze"},
    {"theme_header_foreground_breeze", "theme_header_foreground_backdrop_breeze", "theme_header_foreground_insensitive_breeze", "theme_header_foreground_insensitive_backdrop_breeze"}};
static const Family title = {KCS::Header,
    {"theme_titlebar_background_breeze", "theme_titlebar_background_backdrop_breeze", "theme_titlebar_background_backdrop_breeze", "theme_titlebar_background_backdrop_breeze"},
    {"theme_titlebar_foreground_breeze", "theme_titlebar_foreground_backdrop_breeze", "theme_titlebar_foreground_insensitive_breeze", "theme_titlebar_foreground_insensitive_backdrop_breeze"}};

class Output {
public:
    QJsonObject colors, rgb8, rgb16;
    void put(const char *name, const QColor &color)
    {
        if (!color.isValid()) throw std::runtime_error(std::string("Native KDE returned an invalid colour: ") + name);
        QString key = QString::fromLatin1(name);
        colors.insert(key, color.name(QColor::HexRgb));
        rgb8.insert(key, QJsonArray{color.red(), color.green(), color.blue()});
        auto rgba = color.rgba64();
        rgb16.insert(key, QJsonArray{rgba.red(), rgba.green(), rgba.blue()});
    }
};

static QJsonObject readColors(const QString &path)
{
    const QByteArray before = readInput(path);
    auto config = KSharedConfig::openConfig(path, KConfig::SimpleConfig);
    if (!config) throw std::runtime_error("KSharedConfig could not open the selected file");
    // Disabled+backdrop is intentionally Disabled again, exactly as the
    // installed GTKConfig policy; no invented fourth state-effect formula.
    const QPalette::ColorGroup states[] = {QPalette::Active, QPalette::Inactive, QPalette::Disabled, QPalette::Disabled};
    Output output;
    for (const auto &family : families) {
        for (int state = 0; state < 4; ++state) {
            KCS scheme(states[state], family.set, config);
            output.put(family.background[state], scheme.background().color());
            output.put(family.foreground[state], scheme.foreground().color());
        }
    }
    const char *focus[] = {"theme_button_decoration_focus_breeze", "theme_button_decoration_focus_backdrop_breeze",
                          "theme_button_decoration_focus_insensitive_breeze", "theme_button_decoration_focus_backdrop_insensitive_breeze"};
    for (int state = 0; state < 4; ++state)
        output.put(focus[state], KCS(states[state], KCS::Button, config).decoration(KCS::FocusColor).color());
    KCS tooltip(QPalette::Active, KCS::Tooltip, config);
    output.put("tooltip_background_breeze", tooltip.background().color());
    output.put("tooltip_text_breeze", tooltip.foreground().color());
    const bool hasHeader = KCS::isColorSetSupported(config, KCS::Header);
    for (int state = 0; state < 4; ++state) {
        // Header/title insensitive use the Inactive set, as GTKConfig does.
        KCS scheme(state ? QPalette::Inactive : QPalette::Active,
                   hasHeader ? KCS::Header : KCS::Window, config);
        output.put(header.background[state], scheme.background().color());
        output.put(header.foreground[state], scheme.foreground().color());
        if (hasHeader) {
            output.put(title.background[state], scheme.background().color());
            output.put(title.foreground[state], scheme.foreground().color());
        } else {
            KConfigGroup wm(config, QStringLiteral("WM"));
            output.put(title.background[state], wm.readEntry(state ? "inactiveBackground" : "activeBackground", QColor()));
            output.put(title.foreground[state], wm.readEntry(state ? "inactiveForeground" : "activeForeground", QColor()));
        }
    }
    if (readInput(path) != before) throw std::runtime_error("Selected scheme changed during native colour read");
    QJsonObject provenance{
        {"path", path}, {"sha256", digest(before)}, {"kind", "native_kcolorscheme_selected_file"},
        {"qt_version", QString::fromLatin1(qVersion())}, {"kf_colorscheme_version", QStringLiteral(KCOLORSCHEME_VERSION_STRING)},
        {"gtkconfig_policy_version", "6.3.4"},
        {"gtkconfig_policy_url", "https://github.com/KDE/kde-gtk-config/blob/v6.3.4/kded/configvalueprovider.cpp"},
        {"gtkconfig_policy_source_sha256", "fb3e403291fb667f2495e967772ec7b374bedef661793488c5adc51b55197eee"},
        {"open_mode", "KSharedConfig::openConfig(absolute, KConfig::SimpleConfig)"},
        {"disabled_backdrop", "KColorScheme(Disabled), identical policy to Disabled; not a composed approximation"},
        {"header_insensitive", "Inactive Header, or Inactive Window when no Header set"},
        {"titlebar", hasHeader ? "Header active/inactive" : "WM active/inactive entries; invalid/missing colour refused"},
        {"tooltip", "Active Tooltip in every state"},
        {"unspecified_scheme_roles", "Native KColorScheme API defaults, without theme-local RGB fallback"},
    };
    return {{"status", "ok"}, {"colors", output.colors}, {"rgb8", output.rgb8}, {"rgb16", output.rgb16},
            {"origin", provenance}, {"gui_started", false}, {"host_changed", false}, {"config_written", false}};
}

int main(int argc, char **argv)
{
    QCoreApplication app(argc, argv);
    QJsonObject result;
    int code = 0;
    try {
        const auto args = app.arguments();
        if (args.size() != 3 || args[1] != QStringLiteral("--config") || !QDir::isAbsolutePath(args[2]))
            throw std::runtime_error("Use --config /absolute/selected.colors");
        result = readColors(args[2]);
    } catch (const std::exception &error) {
        result = {{"status", "unavailable"}, {"reason", QString::fromUtf8(error.what())},
                  {"gui_started", false}, {"host_changed", false}, {"config_written", false}};
        code = 2;
    }
    const QByteArray bytes = QJsonDocument(result).toJson(QJsonDocument::Compact) + '\n';
    ssize_t done = 0;
    while (done < bytes.size()) {
        ssize_t count = ::write(STDOUT_FILENO, bytes.constData() + done, bytes.size() - done);
        if (count < 0 && errno == EINTR) continue;
        if (count <= 0) return 2;
        done += count;
    }
    return code;
}
