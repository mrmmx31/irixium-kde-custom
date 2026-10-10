// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-2.0-or-later
// This limits the decoder's work; it is NOT a security sandbox.
#include <QBuffer>
#include <QFile>
#include <QGuiApplication>
#include <QImageReader>
#include <QImage>
#include <QJsonDocument>
#include <QJsonObject>
#include <QStringDecoder>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/resource.h>
#include <unistd.h>
#include <cstdio>

static int output(const QJsonObject &o) {
    const auto bytes = QJsonDocument(o).toJson(QJsonDocument::Compact);
    return std::fwrite(bytes.constData(),1,bytes.size(),stdout) == size_t(bytes.size()) ? 0 : 1;
}
static int unsupported(const QString &m) { return output({{"kind","unsupported"},{"message",m}}); }
int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    const struct rlimit cpu{2,3}; setrlimit(RLIMIT_CPU, &cpu);
    const struct rlimit core{0,0}; setrlimit(RLIMIT_CORE, &core);
    qputenv("QT_QPA_PLATFORM", "offscreen");
    QGuiApplication app(argc,argv);
    QImageReader::setAllocationLimit(128);
    constexpr qint64 maxBytes = 16*1024*1024;
    constexpr qint64 textBytes = 256*1024;
    const QByteArray path = QFile::encodeName(QString::fromLocal8Bit(argv[1]));
    const int fd = ::open(path.constData(), O_RDONLY | O_NONBLOCK | O_CLOEXEC);
    if (fd < 0) return unsupported(QStringLiteral("File could not be opened for reading."));
    struct stat st{};
    if (::fstat(fd,&st) != 0 || !S_ISREG(st.st_mode)) { ::close(fd); return unsupported(QStringLiteral("Only regular local files can be previewed.")); }
    if (st.st_size < 0 || st.st_size > maxBytes) { ::close(fd); return unsupported(QStringLiteral("Preview limit: 16 MiB per file.")); }
    QFile file;
    if (!file.open(fd,QIODevice::ReadOnly,QFileDevice::AutoCloseHandle)) { ::close(fd); return 1; }
    QByteArray data = file.read(maxBytes+1);
    if (file.error() != QFileDevice::NoError || data.size() > maxBytes) return unsupported(QStringLiteral("File changed or exceeded the preview limit."));
    QBuffer input(&data); input.open(QIODevice::ReadOnly);
    QImageReader reader(&input); reader.setAutoTransform(true);
    const auto format = reader.format().toLower();
    const QList<QByteArray> allowed{"png","jpeg","jpg","bmp","gif","webp"};
    if (allowed.contains(format)) {
        const auto size = reader.size();
        if (!size.isValid() || qint64(size.width())*size.height() > 40'000'000) return unsupported(QStringLiteral("Image dimensions exceed the 40-megapixel limit."));
        reader.setScaledSize(size.scaled(1600,1200,Qt::KeepAspectRatio));
        const QImage image = reader.read();
        if (image.isNull()) return unsupported(QStringLiteral("Image decoder rejected this file."));
        QByteArray png; QBuffer buffer(&png); buffer.open(QIODevice::WriteOnly);
        if (!image.save(&buffer,"PNG") || png.size() > 8*1024*1024) return unsupported(QStringLiteral("Decoded image exceeds the output limit."));
        return output({{"kind","image"},{"png",QString::fromLatin1(png.toBase64())},{"first_frame_only",true}});
    }
    const auto sample = data.first(qMin<qsizetype>(data.size(),textBytes));
    int controls = 0;
    for (unsigned char c : sample) { if (c == 0) return unsupported(QStringLiteral("Binary file; no preview renderer for this format.")); if (c < 32 && c != 9 && c != 10 && c != 13 && c != 12) ++controls; }
    if (controls > qMax<qsizetype>(2,sample.size()/100)) return unsupported(QStringLiteral("Binary file; no preview renderer for this format."));
    QStringDecoder decoder(QStringDecoder::Utf8);
    QString text = decoder.decode(sample);
    if (decoder.hasError()) text = QString::fromLatin1(sample);
    if (data.size() > textBytes) text += QStringLiteral("\n\n[Preview truncated at 256 KiB.]");
    return output({{"kind","text"},{"text",text},{"truncated",data.size()>textBytes}});
}
