import uuid

from TTS import TTService

temp_filepath = "F:\\AI\\DigitalMan\\Files\\"

char_name = {
    'paimon': ['TTS/models/paimon6k.json', 'TTS/models/paimon6k_390k.pth', 'character_paimon', 1],
    'yunfei': ['TTS/models/yunfeimix2.json', 'TTS/models/yunfeimix2_53k.pth', 'character_yunfei', 1.1],
    'catmaid': ['TTS/models/catmix.json', 'TTS/models/catmix_107k.pth', 'character_catmaid', 1.2]
}

tts = TTService.TTService(*char_name['paimon'])
wavfile = "{uuid}.wav"
def gen_voice(resp_text, senti_or=None):
    tmp_proc_file = wavfile.format(uuid=uuid.uuid1())
    tts.read_save(resp_text, temp_filepath + tmp_proc_file, tts.hps.data.sampling_rate)

    return tmp_proc_file

if __name__ == '__main__':
    print(gen_voice('欢迎石头送的小心心'))
