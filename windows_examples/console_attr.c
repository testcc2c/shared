/**
 * Display information about console attributes
 *
 * Some functions:
 * BOOL FillConsoleOutputAttribute(HANDLE hStdout, WORD Attributes, DWORD nLen, COORD pos, DWORD *pdwWritten);
 * BOOL FillConsoleOutputCharacter(HANDLE hStdout, CHAR cFill, DWORD nLen, COORD pos, DWORD *pdwWritten);
 * BOOL SetConsoleTextAttribute(HANDLE hStdout, WORD Attributes);
 *
 * Attributes:
 * 0x0001 : FOREGROUND_BLUE, Text color contains blue.
 * 0x0002 : FOREGROUND_GREEN, Text color contains green.
 * 0x0004 : FOREGROUND_RED, Text color contains red.
 * 0x0008 : FOREGROUND_INTENSITY, Text color is intensified.
 * 0x0010 : BACKGROUND_BLUE, Background color contains blue.
 * 0x0020 : BACKGROUND_GREEN, Background color contains green.
 * 0x0040 : BACKGROUND_RED, Background color contains red.
 * 0x0080 : BACKGROUND_INTENSITY, Background color is intensified.
 * 0x0100 : COMMON_LVB_LEADING_BYTE, Leading byte.
 * 0x0200 : COMMON_LVB_TRAILING_BYTE, Trailing byte.
 * 0x0400 : COMMON_LVB_GRID_HORIZONTAL, Top horizontal
 * 0x0800 : COMMON_LVB_GRID_LVERTICAL, Left vertical.
 * 0x1000 : COMMON_LVB_GRID_RVERTICAL, Right vertical.
 * 0x4000 : COMMON_LVB_REVERSE_VIDEO, Reverse foreground and background attribute.
 * 0x8000 : COMMON_LVB_UNDERSCORE, Underscore.
 */

#include <windows.h>
#include <stdlib.h>
#include <stdio.h>

/**
 * Print last Windows error
 */
static void print_winerr(const char *message)
{
    DWORD dwLastErr;
    LPTSTR lpLastErrMsgBuf = NULL;

    dwLastErr = GetLastError();
    if(!FormatMessage( 
        FORMAT_MESSAGE_ALLOCATE_BUFFER|FORMAT_MESSAGE_FROM_SYSTEM|FORMAT_MESSAGE_IGNORE_INSERTS,
        NULL, dwLastErr,
        MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
        (LPTSTR)&lpLastErrMsgBuf, 0, NULL)
    ) {
        lpLastErrMsgBuf = NULL;
    }
    printf("%s: error %lu, %s\n", message, dwLastErr,
        lpLastErrMsgBuf ? lpLastErrMsgBuf : "(unknown)");
    if (lpLastErrMsgBuf) {
        LocalFree(lpLastErrMsgBuf);
    }
}

int main()
{
    HANDLE hStdout;
    CONSOLE_SCREEN_BUFFER_INFO csbiInfo;
    int i;

    AllocConsole();

    hStdout = GetStdHandle(STD_OUTPUT_HANDLE); 
    if(hStdout == INVALID_HANDLE_VALUE){
        print_winerr("Unable to get hStdout");
        return 1;
    }
    if(!GetConsoleScreenBufferInfo(hStdout, &csbiInfo)){
        print_winerr("GetConsoleScreenBufferInfo");
        return 1;
    }
    SetConsoleTextAttribute(hStdout, 0x1A);
    printf("Console size %d x %d\n", csbiInfo.dwSize.X, csbiInfo.dwSize.Y);

    /* Foreground colors */
    for(i = 0; i < 16; i++) {
        SetConsoleTextAttribute(hStdout, i);
        printf("[%X]", i);
    }
    printf("\n");

    /* Background colors */
    for(i = 0; i < 16; i++) {
        SetConsoleTextAttribute(hStdout, (i * 16) | 7);
        printf("[%x]", i);
    }
    printf("\n");
    SetConsoleTextAttribute(hStdout, 0x07);

    MessageBoxW(NULL, L"The colors are displayed on the console", L"Console Attributes", MB_ICONINFORMATION | MB_OK);
    FreeConsole();
    return 0;
}
