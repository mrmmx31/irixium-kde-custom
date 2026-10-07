// SPDX-License-Identifier: MIT
#include <QApplication>
#include <QFile>
#include <QLibrary>
#include <QIcon>
#include <QImage>
#include <QPixmap>
#include <iostream>
int main(int argc,char **argv) {
 QApplication app(argc,argv);
 if(argc!=3)return 2;
 std::cerr<<"load Kate library\n"; QLibrary kate(argv[1]);if(!kate.load()){std::cerr<<kate.errorString().toStdString();return 3;}
 std::cerr<<"compare resource\n"; QFile expected(argv[2]),actual(":/icons/icons/sc-apps-git.svg");
 if(!expected.open(QIODevice::ReadOnly)||!actual.open(QIODevice::ReadOnly)||expected.readAll()!=actual.readAll())return 4;
 using Icon=QIcon(*)();auto git=reinterpret_cast<Icon>(kate.resolve("_Z7gitIconv"));if(!git)return 5;
 std::cerr<<"render Git icon\n"; QIcon ours(argv[2]),rendered=git();
 for(int size:{16,24,32}){QImage a=ours.pixmap(size,size).toImage(),b=rendered.pixmap(size,size).toImage();if(a.isNull()||a!=b)return 6;}
 std::cout<<"Kate gitIcon(): recurso próprio e pixels idênticos em 16/24/32 px\n";
 return 0;
}
