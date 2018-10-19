from pyperclip import paste
from sys import argv
import os
from zlib import crc32
from pathlib import Path, PurePath
import ctypes
MessageBox = ctypes.windll.user32.MessageBoxW
from progressbar import ProgressBar, Counter, Timer

HASH_SIZE_PERCENT = 10
MSG_TITLE = 'Duplicate Finder'
FOLDER = ''


def main():
    def file_rel(fullpath: str) -> str:
        ''' Returns relative path '''
        return os.path.relpath(fullpath, FOLDER)

    # Get path from command-line or clipboard:
    try:
        FOLDER = argv[1]
    except IndexError:
        FOLDER = paste()
    except:
        raise

    # Check if folder looks like path:
    if FOLDER.find(':\\') != 1:
        input(f'Wrong folder:\r\n\r\n{FOLDER}\n\nPress Enter to exit')
        exit()

    print(f'Searching for duplicates in {FOLDER}\n')

    alg = int(
        input('Algorythm:\n' + '0 - Cancel\n' + '1 - By size\n' +
              f'2 - By hash of first {HASH_SIZE_PERCENT} percent of file\n' +
              '3 - By hash of full file\n\n' + 'Choice: '))

    if alg == 0: return

    dups = []
    dups_final = []
    files = {}
    hashes = []

    pathlist = Path(FOLDER).rglob('*')

    widgets = ['Processed: ', Counter(), ' files (', Timer(), ')']
    pbar = ProgressBar(widgets=widgets)
    for fi in pbar(pathlist):
        # Skip folders:
        if fi.is_file():
            filesize = fi.stat().st_size
            if filesize in files:
                # print(file_rel(str(fi)))
                # Collect all files with known size:
                dups.append(str(fi))
            else:
                # Collect unique file size and file:
                files.update({filesize: str(fi)})

    # Now we have list and dictionary:
    # {files} - files with unique size
    # [dups] - files with duplicate sizes
    print('\nDuplicates by size:')
    print(*list(map(file_rel, dups)), sep='\n')
    print(f'Total: {len(dups)}')

    if alg == 1:
        # We already have duplicates
        dups_final = dups
    elif alg == 2:
        print('Now compare hashes')
        # First HASH_SIZE_PERCENT of files
        widgets = ['Processed: ', Counter(), ' files (', Timer(), ')']
        pbar = ProgressBar(widgets=widgets)
        for fi in pbar(dups):
            file_size = os.stat(fi).st_size
            read_limit = int(file_size / 100 * HASH_SIZE_PERCENT)
            with open(fi, 'rb') as f:
                hash_dup = crc32(f.read(read_limit)) & 0xFFFFFFFF
            if hash_dup in hashes:
                dups_final.append(fi)
            else:
                # Calculate hash of file with same size from {files}
                with open(files[file_size], 'rb') as f:
                    hash_prev = crc32(f.read(read_limit)) & 0xFFFFFFFF
                hashes.append(hash_prev)
                if hash_dup == hash_prev:
                    # It's the same file:
                    dups_final.append(fi)
                else:
                    # Same size but different file:
                    hashes.append(hash_dup)
    elif alg == 3:
        # By hash of full file:
        widgets = ['Processed: ', Counter(), ' files (', Timer(), ')']
        pbar = ProgressBar(widgets=widgets)
        for fi in pbar(dups):
            file_size = os.stat(fi).st_size
            with open(fi, 'rb') as f:
                hash_dup = crc32(f.read()) & 0xFFFFFFFF
            if hash_dup in hashes:
                dups_final.append(fi)
            else:
                # Calculate hash of file with same size from {files}
                with open(files[file_size], 'rb') as f:
                    hash_prev = crc32(f.read()) & 0xFFFFFFFF
                hashes.append(hash_prev)
                if hash_dup == hash_prev:
                    # It's the same file:
                    dups_final.append(fi)
                else:
                    # Same size but different file:
                    hashes.append(hash_dup)
    else:
        print('WTF?')

    # Final list of duplicates:
    print('\nFinal list of duplicates:')
    print(*list(map(file_rel, dups_final)), sep='\n')
    print(f'Final total: {len(dups_final)}')
    MessageBox(None, 'Search for duplicates is complete', MSG_TITLE, 64 + 4096)

    if len(dups_final) > 0:
        if input('\nDelete duplicates? (Y/n): ') == 'Y':
            for dup in dups_final:
                try:
                    os.remove(dup)
                except:
                    print(f'Can\'t delete file: {dup}')
                    raise
        else:
            exit()


if __name__ == '__main__':
    main()
