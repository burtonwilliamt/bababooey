"""Helper to sync data to/from server."""
import enum
import os
import shelve
import subprocess

from settings import REMOTE_HOST_NAME, REMOTE_SFX_DATA, LOCAL_SFX_DATA


class Direction(enum.Enum):
    DOWNLOAD = 1
    UPLOAD = 2


def relative_path_effects(shelve_path: str) -> list:
    """Loads the effects from shelve_path and replaces files_are_relative_to with new_prefix."""
    with shelve.open(shelve_path) as s:
        effects = s['data']
    return effects


def transfer_sfx(direction: Direction):
    print('Downloading the remote sfx metadata to compare.')
    #subprocess.run([
    #'scp',
    #f'{REMOTE_HOST_NAME}:{str(REMOTE_DATA_FOLDER.joinpath("sfx_data"))}',
    #'/tmp/sfx_data'
    #],
    #check=True)

    print('Extracting the downloaded metadata')
    remote_effects = relative_path_effects(shelve_path='/tmp/sfx_data',)
    print('Extracting the local metadata')
    local_effects = relative_path_effects(shelve_path=LOCAL_SFX_DATA)

    if direction == Direction.DOWNLOAD:
        source = remote_effects
        destination = local_effects
    elif direction == Direction.UPLOAD:
        source = local_effects
        destination = remote_effects

    missing = [sfx for sfx in source if sfx not in destination]
    to_be_overwritten = [sfx for sfx in destination if sfx not in source]

    if len(to_be_overwritten) > 0:
        print(
            f'Looks like {len(to_be_overwritten)} effects would be overwritten:'
        )
        for sfx in to_be_overwritten:
            print(f'\t{sfx.name}')
        answer = input('Overwrite these sfx? [y|yes] ')
        if answer.lower() not in {'y', 'yes'}:
            print('Aborting the copy.')
            return

    if len(missing) == 0:
        print('No missing sound effects detected.')
        return

    print(f'Adding {len(missing)} missing sound effects.')
    if direction == Direction.UPLOAD:
        subprocess.run([
            'scp',
            LOCAL_SFX_DATA,
            f'{REMOTE_HOST_NAME}:{REMOTE_SFX_DATA}',
        ],
                       check=True)
    elif direction == Direction.DOWNLOAD:
        subprocess.run([
            'cp',
            '/tmp/sfx_data',
            LOCAL_SFX_DATA,
        ], check=True)

    # Handle missing files
    if direction == Direction.DOWNLOAD:
        for sfx in missing:
            print(f'\t{sfx.name} have_file: {os.path.exists(sfx.file_path)}')

        missing_files = [
            sfx.file_path for sfx in source if not os.path.exists(sfx.file_path)
        ]
        print(f'We\'re missing {len(missing_files)} files.')
        for path in missing_files:
            print(f'\t{path}')
        # TODO: download the missing files

    elif direction == Direction.UPLOAD:
        print('Consider uploading these files: ')
        for sfx in missing:
            print(f'\t{sfx.file_path}')
        # TODO: detect which files the server is missing.


if __name__ == '__main__':
    mode = input('What would you like to do? [upload|download]: ')
    if mode == 'upload':
        transfer_sfx(Direction.UPLOAD)
    elif mode == 'download':
        transfer_sfx(Direction.DOWNLOAD)
