package main

import (
	"fmt"
	"io/ioutil"
	"math"
	"os"
	"path"
	"strconv"
	"strings"
	"syscall"
	"time"
)

func main() {
	if len(os.Args) == 3 {
		backupPruneDays, err := strconv.ParseInt(os.Args[1], 10, 16)
		if err != nil {
			fmt.Printf("Parameter \"PruneDays\" must be a positive (>0) integer! (%s)\n", err.Error())
			os.Exit(1)
		}
		if backupPruneDays <= 0 {
			fmt.Printf("Parameter \"PruneDays\" must be a positive (>0) integer!\n")
			os.Exit(1)
		}
		checkBackupFiles(os.Args[2], int16(backupPruneDays))
	} else {
		fmt.Printf("%s <PruneDays> <BackupDirectory>\n", os.Args[0])
		os.Exit(1)
	}
	os.Exit(0)
}

func getDayFromNow(BackupFile string) (int16, error) {
	var fileStat syscall.Stat_t
	err := syscall.Stat(BackupFile, &fileStat)
	if err != nil {
		return 0, err
	}
	fileUnixTimeSec, fileUnixTimeMsec := fileStat.Ctim.Unix()
	fileTime := time.Unix(fileUnixTimeSec, fileUnixTimeMsec)
	fileTimeSince := time.Since(fileTime)
	return int16(math.Floor(fileTimeSince.Hours()/24) + 1), nil
}

func checkBackupFiles(BackupDir string, BackupPruneDays int16) {
	backupFiles, err := ioutil.ReadDir(BackupDir)
	if err != nil {
		fmt.Printf("Could not read directory \"%s\"! (%s)\n", BackupDir, err.Error())
		os.Exit(1)
	}
	backupFilesCount, backupFilesKept, backupFilesRemoved := 0, 0, 0
	for _, backupFile := range backupFiles {
		if !backupFile.IsDir() && strings.Contains(backupFile.Name(), ".vma") {
			backupFilesCount++
			backupFilePath := path.Join(BackupDir, backupFile.Name())
			backupDays, err := getDayFromNow(backupFilePath)
			if err != nil {
				fmt.Printf("Could not get file time for \"%s\"! (%s)\n", backupFilePath, err.Error())
			} else {
				if backupDays > BackupPruneDays {
					fmt.Printf("Backup \"%s\" is \"%d\" days old, limit is \"%d\", removing!\n", backupFilePath, backupDays, BackupPruneDays)
					backupFilesRemoved++
					err := os.Remove(backupFilePath)
					if err != nil {
						fmt.Printf("Could not remove file \"%s\"! (%s)\n", backupFilePath, err.Error())
					}
				} else {
					backupFilesKept++
				}
			}
		}
	}
	fmt.Printf("Processing finished: %d Files Processed, %d Files Kept, %d Files Removed.\n", backupFilesCount, backupFilesKept, backupFilesRemoved)
}

//# EOF