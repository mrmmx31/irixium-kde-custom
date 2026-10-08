/* SPDX-FileCopyrightText: 2026 mrmmx31
 * SPDX-License-Identifier: GPL-3.0-or-later
 * Original Wine theme utility. Win32 declarations avoid a Wine SDK dependency.
 */
typedef unsigned long DWORD;
typedef int BOOL;
typedef long HRESULT;
typedef __WCHAR_TYPE__ WCHAR;
typedef void *HANDLE;
typedef const WCHAR *LPCWSTR;
typedef WCHAR *LPWSTR;
#define API __declspec(dllimport)
API HANDLE GetStdHandle(DWORD);
API BOOL WriteFile(HANDLE,const void *,DWORD,DWORD *,void *);
API void ExitProcess(DWORD);
API LPWSTR GetCommandLineW(void);
API LPWSTR *CommandLineToArgvW(LPCWSTR,int *);
API HANDLE LoadLibraryW(LPCWSTR);
API void *GetProcAddress(HANDLE,const char *);
API DWORD GetLastError(void);
API BOOL IsThemeActive(void);
API HRESULT GetCurrentThemeName(LPWSTR,int,LPWSTR,int,LPWSTR,int);
API DWORD GetSysColor(int);
typedef HRESULT (*OpenTheme)(LPCWSTR,LPCWSTR,LPCWSTR,HANDLE *,DWORD);
typedef HRESULT (*Apply)(HANDLE,char *,HANDLE);
typedef HRESULT (*CloseTheme)(HANDLE);

void *memset(void *destination,int value,__SIZE_TYPE__ count) {
    volatile unsigned char *p=(volatile unsigned char *)destination;
    while(count--)*p++=(unsigned char)value;
    return destination;
}

static void out(const char *s) {
    DWORD n=0,written=0;while(s[n])++n;
    WriteFile(GetStdHandle((DWORD)-11),s,n,&written,0);
}
static void number(DWORD n) {
    char digits[11];int i=10;digits[i]=0;
    do {digits[--i]=(char)('0'+n%10);n/=10;}while(n);
    out(digits+i);
}
static void string(LPCWSTR s) {
    char c[7];const char *hex="0123456789abcdef";
    out("\"");
    while(*s) {
        unsigned int v=*s++;
        if(v=='"'||v=='\\'){c[0]='\\';c[1]=(char)v;c[2]=0;out(c);}
        else if(v>=32&&v<127){c[0]=(char)v;c[1]=0;out(c);}
        else {c[0]='\\';c[1]='u';for(int i=0;i<4;++i)c[2+i]=hex[(v>>(12-i*4))&15];c[6]=0;out(c);}
    }
    out("\"");
}
static BOOL equal(LPCWSTR a,LPCWSTR b) {while(*a&&*a==*b){++a;++b;}return *a==*b;}
static void info(void) {
    WCHAR path[1024]={0},color[256]={0},size[256]={0};
    HRESULT result=GetCurrentThemeName(path,1024,color,256,size,256);
    out("{\"active\":");out(IsThemeActive()?"true":"false");
    out(",\"result\":");number((DWORD)result);
    out(",\"path\":");string(path);out(",\"color\":");string(color);out(",\"size\":");string(size);
    out(",\"system_colors\":[");
    for(int i=0;i<31;++i){if(i)out(",");number(GetSysColor(i));}
    out("]}\n");
}

void mainCRTStartup(void) {
    int argc=0;LPWSTR *argv=CommandLineToArgvW(GetCommandLineW(),&argc);
    if(argc<2){out("{\"error\":\"Use inspect, apply <msstyles>, or clear\"}\n");ExitProcess(2);}
    if(equal(argv[1],L"inspect")){info();ExitProcess(0);}
    HANDLE lib=LoadLibraryW(L"uxtheme.dll");
    OpenTheme open=(OpenTheme)GetProcAddress(lib,"OpenThemeFile");
    Apply apply=(Apply)GetProcAddress(lib,"ApplyTheme");
    CloseTheme close=(CloseTheme)GetProcAddress(lib,"CloseThemeFile");
    /* Wine exports these three documented-in-source APIs by ordinal. */
    if(!open)open=(OpenTheme)GetProcAddress(lib,(const char *)(__UINTPTR_TYPE__)2);
    if(!close)close=(CloseTheme)GetProcAddress(lib,(const char *)(__UINTPTR_TYPE__)3);
    if(!apply)apply=(Apply)GetProcAddress(lib,(const char *)(__UINTPTR_TYPE__)4);
    if(!open||!apply||!close){out("{\"error\":\"Wine theme API unavailable\"}\n");ExitProcess(3);}
    HANDLE theme=0;HRESULT result=0;char reserved=0;
    if(equal(argv[1],L"apply")&&argc>=3)result=open(argv[2],argc>=4?argv[3]:0,argc>=5?argv[4]:0,&theme,0);
    else if(!equal(argv[1],L"clear")){out("{\"error\":\"Invalid operation\"}\n");ExitProcess(2);}
    if(result<0){out("{\"error\":\"OpenThemeFile failed\",\"result\":");number((DWORD)result);out("}\n");ExitProcess(4);}
    result=apply(theme,&reserved,0);
    if(theme)close(theme);
    if(result<0){out("{\"error\":\"ApplyTheme failed\",\"result\":");number((DWORD)result);out("}\n");ExitProcess(5);}
    info();ExitProcess(0);
}
