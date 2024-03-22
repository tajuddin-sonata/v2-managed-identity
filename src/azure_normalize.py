from typing import List, Union
import datetime

displayText="displayText"
offsetInTicks="offsetInTicks"
durationInTicks="durationInTicks"


class Model:
    def __init__(self, name: str, version: str, arch: str):
        self.name = name
        self.version = version
        self.arch = arch

class ModelInfo:
    def __init__(self, model: Model):
        self.model = model

class Media:
    def __init__(self, media_type: str, external_id: str):
        self.media_type: str = media_type
        self.external_id: str = external_id

class Options:
    def __init__(self, opt):
        self.channel_map = opt['channel_map']

class Metadata:
    def __init__(self, transaction_key: str, request_id: str, sha256: str, created: datetime, duration: float, channels: int, models: List[str], model_info: ModelInfo, media_type: Media, speaker_names: Options):
        self.transaction_key = transaction_key
        self.request_id = request_id
        self.sha256 = sha256
        self.created = created
        self.duration = duration
        self.channels = channels
        self.models = models
        self.model_info = model_info
        self.media = media_type
        self.speaker_names = speaker_names

class Word:
    def __init__(self, word, index, confidence):
        self.word_text = word[displayText]
        self.word_index = index
        self.confidence = confidence
        self.start_time = word[offsetInTicks] / 10000000
        self.end_time = (word[durationInTicks] + word[offsetInTicks]) / 10000000

class Turn:
    def __init__(self, index, turn_text, word_array,channel_index):
        self.words_array = word_array
        self.turn_index = index
        self.channel_index = channel_index
        self.speaker_index = 0
        self.turn_text = turn_text
        self.start_time = self.words_array[0].start_time
        self.end_time = self.words_array[-1].end_time
        self.source = 'Agent' if channel_index == 0 else 'Caller'
        
def normalize_azure(azure_stt_response, transaction_id, model, version, opts):
    if not azure_stt_response['recognizedPhrases']:
        # If no recognized phrases, return metadata with an empty turns_array
        models = [model]
        m1 = Model("base", version, "base")
        m2 = ModelInfo(m1)
        m3 = Media("voice", "")
        channels = 0
        meta_obj = Metadata(transaction_id, transaction_id, "", azure_stt_response['timestamp'],  (azure_stt_response['durationInTicks'] / 10000000), channels, models, m2, m3, opts)
        json_data = generate_json(meta_obj.__dict__, [])
        return json_data

    azure_turn_index = 1
    azure_turns_array = []
    azure_words_array = []
    azure_turn_text = ""
    word_index = 1

    models = [model]
    m1 = Model("base", version, "base")
    m2 = ModelInfo(m1)
    m3 = Media("voice", "")

    channel_numbers = set()
    for phrase in azure_stt_response['combinedRecognizedPhrases']:
        channel_numbers.add(phrase['channel'])

    # Counting the unique channel numbers
    channels = len(channel_numbers)
    meta_obj = Metadata(transaction_id, transaction_id, "", azure_stt_response['timestamp'], (azure_stt_response['durationInTicks'] / 10000000), channels, models, m2, m3, opts)
    sorted_recognized_phrases = sorted(azure_stt_response['recognizedPhrases'], key=lambda x: x['offsetInTicks'])
    prev_channel = sorted_recognized_phrases[0]['channel']
    for phrase in sorted_recognized_phrases:
        current_channel = phrase['channel']
        if ((sorted_recognized_phrases.index(phrase) == len(sorted_recognized_phrases) - 1 or current_channel != prev_channel) and azure_words_array != []):
            turn_obj = Turn(azure_turn_index, azure_turn_text, azure_words_array, prev_channel)
            azure_turns_array.append(turn_obj)
            azure_turn_index = azure_turn_index + 1
            azure_turn_text = ""
            azure_words_array = []
            word_index = 1

        confidence = phrase['nBest'][0]['confidence']
        azure_turn_text += phrase['nBest'][0]['display']

        for azure_word in phrase['nBest'][0]['displayWords']:
            w = Word(azure_word, word_index, confidence)
            word_index = word_index + 1
            azure_words_array.append(w)
        prev_channel = current_channel
    json_data = generate_json(meta_obj.__dict__, azure_turns_array)
    return json_data

def generate_json(metadata, turns_array):
    metadata_copy = metadata.copy()  # Make a copy of metadata to avoid modifying the original dict
    model_info_dict = metadata_copy['model_info'].__dict__
    model_info_key = list(model_info_dict.keys())[0]  # Get the UUID key from the model_info dict

    # Replace 'model' key with the first element of 'models' list
    model_info_dict[metadata['models'][0]] = model_info_dict.pop(model_info_key)

    return {
        "metadata": {
            **metadata_copy,
            "models": metadata_copy['models'],
            "model_info": model_info_dict,
            "speaker_names": metadata_copy['speaker_names'].channel_map
        },
        "turns_array": [
            {
                "turn_index": turn.turn_index,
                "turn_text": turn.turn_text,
                "source": turn.source,
                "channel_index": turn.channel_index,
                "source_index": turn.speaker_index,
                "start_time": turn.start_time,
                "end_time": turn.end_time,
                "words_array": [
                    {
                        "word_index": word.word_index,
                        "word_text": word.word_text,
                        "confidence": word.confidence,
                        "start_time": word.start_time,
                        "end_time": word.end_time
                    }
                    for word in turn.words_array
                ]
            }
            for turn in turns_array
        ]
    }


def custom_serializer(obj):
    if isinstance(obj, Model):
        return obj.__dict__
    elif isinstance(obj, ModelInfo):
        return obj.__dict__
    elif isinstance(obj, Media):
        return obj.__dict__
    elif isinstance(obj, Options):
        return obj.__dict__
    else:
        raise TypeError("Object of type '{}' is not JSON serializable".format(type(obj).__name__))
    
def normalize(azure_stt_response, transcription_id, model, version,options):
    opts = Options(options)
    return normalize_azure(azure_stt_response, transcription_id, model, version,opts)

