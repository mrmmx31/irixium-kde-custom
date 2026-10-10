/* SPDX-FileCopyrightText: 2026 mrmmx31
 * SPDX-License-Identifier: GPL-3.0-or-later
 * Native Win32 controls for Wine styling/input verification, not a mockup.
 */
#define mainCRTStartup unused_theme_entry
#include "theme.c"
#undef mainCRTStartup
typedef unsigned int UINT;
typedef __UINTPTR_TYPE__ WPARAM;
typedef __INTPTR_TYPE__ LPARAM;
typedef __INTPTR_TYPE__ LRESULT;
typedef struct {int x,y;} POINT;
typedef struct {int left,top,right,bottom;} RECT;
typedef struct {HANDLE hwnd;UINT message;WPARAM wParam;LPARAM lParam;DWORD time;POINT pt;DWORD private_value;} MSG;
typedef LRESULT (*WNDPROC)(HANDLE,UINT,WPARAM,LPARAM);
typedef struct {UINT style;WNDPROC proc;int clsExtra,wndExtra;HANDLE instance,icon,cursor,background;LPCWSTR menu,name;} WNDCLASS;
typedef struct {HANDLE dc;BOOL erase;RECT rect;BOOL restore,update;unsigned char reserved[32];} PAINTSTRUCT;
typedef struct {DWORD size,classes;} INITCOMMON;
API HANDLE GetModuleHandleW(LPCWSTR);
API unsigned short RegisterClassW(const WNDCLASS *);
API HANDLE CreateWindowExW(DWORD,LPCWSTR,LPCWSTR,DWORD,int,int,int,int,HANDLE,HANDLE,HANDLE,void *);
API LRESULT DefWindowProcW(HANDLE,UINT,WPARAM,LPARAM);
API BOOL ShowWindow(HANDLE,int);
API BOOL UpdateWindow(HANDLE);
API BOOL GetMessageW(MSG *,HANDLE,UINT,UINT);
API BOOL TranslateMessage(const MSG *);
API LRESULT DispatchMessageW(const MSG *);
API void PostQuitMessage(int);
API BOOL DestroyWindow(HANDLE);
API LRESULT SendMessageW(HANDLE,UINT,WPARAM,LPARAM);
API BOOL EnableWindow(HANDLE,BOOL);
API HANDLE LoadCursorW(HANDLE,LPCWSTR);
API HANDLE GetSysColorBrush(int);
API HANDLE CreateFontW(int,int,int,int,int,DWORD,DWORD,DWORD,DWORD,DWORD,DWORD,DWORD,DWORD,LPCWSTR);
API BOOL SetWindowTextW(HANDLE,LPCWSTR);
API BOOL InitCommonControlsEx(const INITCOMMON *);
API BOOL SetProcessDPIAware(void);
API BOOL GetWindowRect(HANDLE,RECT *);
API HANDLE OpenThemeData(HANDLE,LPCWSTR);
API BOOL IsThemePartDefined(HANDLE,int,int);
API HRESULT GetThemeFilename(HANDLE,int,int,int,LPWSTR,int);
API HRESULT CloseThemeData(HANDLE);
API HANDLE BeginPaint(HANDLE,PAINTSTRUCT *);
API BOOL EndPaint(HANDLE,const PAINTSTRUCT *);
API BOOL TextOutW(HANDLE,int,int,LPCWSTR,int);
API DWORD SetTextColor(HANDLE,DWORD);
API int SetBkMode(HANDLE,int);

static HANDLE instance,font,status,applyButton,closeButton;
static HANDLE control(HANDLE parent,LPCWSTR klass,LPCWSTR title,DWORD style,int x,int y,int width,int height,int id) {
    HANDLE w=CreateWindowExW(0,klass,title,0x50000000|style,x,y,width,height,parent,(HANDLE)(__UINTPTR_TYPE__)id,instance,0);
    if(w)SendMessageW(w,0x30,(WPARAM)font,1);
    return w;
}
static LRESULT procedure(HANDLE w,UINT message,WPARAM wp,LPARAM lp) {
    if(message==0x01) {
        control(w,L"STATIC",L"Native Win32 controls / IRIX Classic",0,18,16,650,28,1);
        applyButton=control(w,L"BUTTON",L"Apply",0,18,58,130,36,100);
        control(w,L"BUTTON",L"Default",1,162,58,130,36,101);
        HANDLE disabled=control(w,L"BUTTON",L"Disabled",0,306,58,130,36,102);EnableWindow(disabled,0);
        control(w,L"BUTTON",L"Frame",7,18,108,416,134,2);
        HANDLE check=control(w,L"BUTTON",L"Red check",3,36,138,180,28,103);SendMessageW(check,0xf1,1,0);
        control(w,L"BUTTON",L"Unchecked",3,236,138,180,28,104);
        HANDLE radio=control(w,L"BUTTON",L"Blue diamond",9,36,184,190,28,105);SendMessageW(radio,0xf1,1,0);
        control(w,L"BUTTON",L"Unselected",9,236,184,190,28,106);
        control(w,L"EDIT",L"Classic text entry",0x00800080,18,260,416,34,107);
        HANDLE combo=control(w,L"COMBOBOX",L"",0x00200003,18,312,252,180,108);
        SendMessageW(combo,0x143,0,(LPARAM)L"IRIX Classic");SendMessageW(combo,0x143,0,(LPARAM)L"Native application selection");SendMessageW(combo,0x14e,0,0);
        HANDLE progress=control(w,L"msctls_progress32",L"",0,18,360,416,24,109);SendMessageW(progress,0x402,62,0);
        HANDLE list=control(w,L"LISTBOX",L"",0x00a00001,462,58,222,214,110);
        SendMessageW(list,0x180,0,(LPARAM)L"/usr/people");SendMessageW(list,0x180,0,(LPARAM)L"Workstation tools");SendMessageW(list,0x180,0,(LPARAM)L"Native Wine controls");SendMessageW(list,0x186,1,0);
        control(w,L"SCROLLBAR",L"",0,462,290,222,20,111);
        closeButton=control(w,L"BUTTON",L"Exit preview",0,462,360,222,36,113);
        status=control(w,L"STATIC",L"Press Apply: native action, no animation timer",0,18,416,660,26,112);
        return 0;
    }
    if(message==0x111 && (wp&0xffff)==100) {
        SetWindowTextW(status,L"Native Apply action received");out("{\"apply_clicked\":true}\n");return 0;
    }
    if(message==0x111 && (wp&0xffff)==113){DestroyWindow(w);return 0;}
    if(message==0x10){DestroyWindow(w);return 0;}
    if(message==0x02){PostQuitMessage(0);return 0;}
    return DefWindowProcW(w,message,wp,lp);
}

void mainCRTStartup(void) {
    SetProcessDPIAware();
    INITCOMMON init={sizeof(INITCOMMON),0x000000ff};InitCommonControlsEx(&init);
    instance=GetModuleHandleW(0);
    /* Preview font only. The installed style does not override prefix/app fonts. */
    font=CreateFontW(-16,0,0,0,400,0,0,0,1,0,0,0,0,L"Nimbus Sans");
    WNDCLASS klass={0,procedure,0,0,instance,0,LoadCursorW(0,(LPCWSTR)(__UINTPTR_TYPE__)32512),GetSysColorBrush(15),0,L"IRIXClassicWinePreview"};
    if(!RegisterClassW(&klass))ExitProcess(10);
    HANDLE window=CreateWindowExW(0,klass.name,L"IRIX Classic - Wine native controls",0x00cf0000,40,40,730,520,0,0,instance,0);
    if(!window)ExitProcess(11);
    ShowWindow(window,5);UpdateWindow(window);
    out("{\"preview_ready\":true,\"theme_active\":");out(IsThemeActive()?"true":"false");out(",\"parts\":[");
    const WCHAR *classes[]={L"Button",L"Edit",L"ComboBox",L"ScrollBar",L"Tab",L"Progress",L"TrackBar",L"Header",L"ToolBar"};
    int ids[]={1,1,1,1,1,1,1,1,1};
    for(int i=0;i<9;++i) {
        HANDLE theme=OpenThemeData(window,classes[i]);BOOL defined=theme&&IsThemePartDefined(theme,ids[i],0);
        WCHAR bitmap[256]={0};HRESULT found=theme?GetThemeFilename(theme,ids[i],1,3001,bitmap,256):-1;
        if(i)out(",");out("{\"class\":");string(classes[i]);out(",\"defined\":");out(defined?"true":"false");
        out(",\"bitmap\":");if(found>=0)string(bitmap);else out("null");out("}");
        if(theme)CloseThemeData(theme);
    }
    RECT button;GetWindowRect(applyButton,&button);
    out("],\"apply_rect\":[");number(button.left);out(",");number(button.top);out(",");
    number(button.right-button.left);out(",");number(button.bottom-button.top);out("],\"close_rect\":[");
    GetWindowRect(closeButton,&button);number(button.left);out(",");number(button.top);out(",");
    number(button.right-button.left);out(",");number(button.bottom-button.top);out("]}\n");
    MSG message;while(GetMessageW(&message,0,0,0)>0){TranslateMessage(&message);DispatchMessageW(&message);}
    ExitProcess(0);
}
