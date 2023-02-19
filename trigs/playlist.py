import os.path
import glob
import wave
import io


def resolve_playlist(paths):
    """
    Turns an iterable of filesystem paths into an iterable of absolute paths to *.wav files.
    :param paths: An iterable of filesystem paths. Each path can point to a *.wav file, or a directory.
    :return: An iterable of absolute paths to *.wav files.
    """
    paths = list(paths)

    wav_paths = []

    while len(paths) > 0:
        path = os.path.abspath(paths.pop(0))
        if os.path.isdir(path):
            for path in glob.glob(os.path.join(path, "*.wav")):
                wav_paths.append(path)
        elif os.path.splitext(path)[-1] == ".wav":
            wav_paths.append(path)
        else:
            raise ValueError("'resolve_playlist' supports only *.wav files and directories containing them!")

    return sorted(wav_paths)


def load_wav(path, chunk_size=44100):
    """
    Loads the contents of a *.wav file from disk.
    :param path: The path to the *.wav file.
    :param chunk_size: The chunk size with which the file is to be read.
    :return: A tuple (w, c, r, data), where data is a bytes object that contains the audio data, while w is the sample
             width (in bytes), c is th enumber of channels and r is the framerate.
    """
    with wave.open(path, 'rb') as wf:
        c, w, r, _, _, _ = wf.getparams()
        with io.BytesIO() as s:
            while True:
                chunk = wf.readframes(chunk_size)
                if len(chunk) == 0:
                    return w, c, r, s.getvalue()
                s.write(chunk)
