import os

MEDIA_DIRECTORY = os.path.join(os.path.dirname(__file__), 'media')
SCREEN_DIRECTORY = os.path.join(os.path.dirname(__file__), 'screen')


def get_screens():
    # Todo: replace underscores with spaces
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
            if filename.__contains__('_horizontal'):
                split = filename.split('_horizontal')
                if not files.__contains__(split[0] + split[1]):
                    files.append(split[0] + split[1])
            elif filename.__contains__('_vertical'):
                split = filename.split('_vertical')
                if not files.__contains__(split[0] + split[1]):
                    files.append(split[0] + split[1])
            else:
                files.append(filename)
    return files