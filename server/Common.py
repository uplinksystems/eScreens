import os

MEDIA_DIRECTORY = os.path.join(os.path.dirname(__file__), 'media')
SCREEN_DIRECTORY = os.path.join(os.path.dirname(__file__), 'screen')


def get_screens():
    files = []
    for filename in os.listdir(SCREEN_DIRECTORY):
        path = os.path.join(SCREEN_DIRECTORY, filename)
        if os.path.isfile(path):
            files.append(filename)
    return files

def get_media():
    files = []
    for filename in os.listdir(MEDIA_DIRECTORY):
        path = os.path.join(MEDIA_DIRECTORY, filename)
        if os.path.isfile(path):
            if filename.endswith('_horizontal'):
                if not filename[:-11] in files:
                    files.append(filename[:-11])
            elif filename.endswith('_vertical'):
                if not filename[:-9] in files:
                    files.append(filename[:-9])
            else:
                files.append(filename)
    return files