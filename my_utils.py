import re
from googletrans import Translator
import os
import json


def validate_json_structure(data, expected_structure):
    """
    Validate the structure of a JSON object against an expected structure.
    :param data: The JSON object to validate.
    :param expected_structure: A dictionary representing the expected structure.
    :return: A boolean indicating if the structure is valid and a list of errors if any.
    """
    errors = []

    def _validate(data, expected_structure, path=''):
        if isinstance(expected_structure, dict):
            if not isinstance(data, dict):
                errors.append(f"Expected a dict at '{path}', got {type(data).__name__}")
                return

            for key, value in expected_structure.items():
                if key not in data:
                    errors.append(f"Missing key '{key}' at '{path}'")
                else:
                    _validate(data[key], value, f"{path}.{key}" if path else key)

        elif isinstance(expected_structure, list):
            if not isinstance(data, list):
                errors.append(f"Expected a list at '{path}', got {type(data).__name__}")
                return

            if expected_structure:
                for index, item in enumerate(data):
                    _validate(item, expected_structure[0], f"{path}[{index}]")

        elif isinstance(expected_structure, type):
            if not isinstance(data, expected_structure):
                errors.append(f"Expected {expected_structure.__name__} at '{path}', got {type(data).__name__}")

    _validate(data, expected_structure)
    return len(errors) == 0


def convert_back_to_latin(response):
    response = response\
    .replace('抽出部分の法律名','sub_law_name')\
    .replace('抽出された法律の配列','sub_laws')\
    .replace('抽出された法律の内容','sub_law_content')\
    .replace('抽出された契約の名前','sub_chunk_name')\
    .replace('抽出された契約の内容','sub_chunk_content')\
    .replace('抽出部分の説明','sub_explanation')\
    .replace('抽出部分のラベル','sub_label')\
    .replace('結論','Conclusion')\
    .replace('分析','Response')\
    .replace('正しいラベル','TRUE')\
    .replace('間違ったラベル','FALSE')\
    .replace('情報不足のラベル','NEI')
    response=re.sub(r"法律(\d+)の内容", r"Law's content \1", response)
    return response  # Xóa dấu phẩy hoặc ký tự thừa nếu có

def convert_japanese(response):
    response = response\
    .replace('Sub Chunk Name','抽出された契約の名前')\
    .replace('Sub Chunk Content','抽出された契約の内容')\
    .replace('Sub Explanation','抽出部分の説明')\
    .replace('Sub Label','抽出部分のラベル')\
    .replace('Conclusion','結論')\
    .replace('TRUE','正しいラベル')\
    .replace('FALSE','間違ったラベル')\
    .replace('NEI','情報不足のラベル')
    response = re.sub(r'\bSub Law (\d+) Name\b', r'抽出部分の法律名\1', response)
    response = re.sub(r'\bSub Law (\d+) Content\b', r"法律\1の内容", response)
    response = response.replace("Law's name","#抽出部分の法律名")
    response=re.sub(r"Law's content (\d+)", r"法律\1の内容", response)
    return response 

def filter_dataframe(df, name):
    print(f'{name}\'s original length: ',len(df))
    ## delete nan and duplicate
    df = df.dropna(subset=['response'])
    df = df.drop_duplicates()
    print(f'{name}\'s filtered length: ',len(df))
    return df

def convert_to_halfwidth(text):
    # Bảng chuyển đổi từ ký tự full-width (tiếng Nhật) sang ký tự Latin (tiếng Anh)
    translation_table = str.maketrans(
        {
            'ａ': 'a', 'ｂ': 'b', 'ｃ': 'c', 'ｄ': 'd', 'ｅ': 'e', 'ｆ': 'f', 'ｇ': 'g', 'ｈ': 'h', 'ｉ': 'i', 'ｊ': 'j',
            'ｋ': 'k', 'ｌ': 'l', 'ｍ': 'm', 'ｎ': 'n', 'ｏ': 'o', 'ｐ': 'p', 'ｑ': 'q', 'ｒ': 'r', 'ｓ': 's', 'ｔ': 't',
            'ｕ': 'u', 'ｖ': 'v', 'ｗ': 'w', 'ｘ': 'x', 'ｙ': 'y', 'ｚ': 'z',
            'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E', 'Ｆ': 'F', 'Ｇ': 'G', 'Ｈ': 'H', 'Ｉ': 'I', 'Ｊ': 'J',
            'Ｋ': 'K', 'Ｌ': 'L', 'Ｍ': 'M', 'Ｎ': 'N', 'Ｏ': 'O', 'Ｐ': 'P', 'Ｑ': 'Q', 'Ｒ': 'R', 'Ｓ': 'S', 'Ｔ': 'T',
            'Ｕ': 'U', 'Ｖ': 'V', 'Ｗ': 'W', 'Ｘ': 'X', 'Ｙ': 'Y', 'Ｚ': 'Z',
            '０': '0', '１': '1', '２': '2', '３': '3', '４': '4', '５': '5', '６': '6', '７': '7', '８': '8', '９': '9',
            '　': ' ', '．': '.', '，': ',', '：': ':', '；': ';', '！': '!', '？': '?', '＂': '"', '（': '(', '）': ')',
            '－': '-', '＿': '_', '／': '/', '＼': '\\', '＆': '&', '％': '%', '＃': '#', '＊': '*', '＋': '+', '＝': '='
        }
    )
    # Chuyển văn bản từ full-width sang half-width
    return text.translate(translation_table)


def normalize_text(text):
    text=convert_to_halfwidth(text)
    while '\n\n' in text:
        text=text.replace("\n\n",'\n')
    while '  ' in text:
        text=text.replace("  ",' ')   
    while '　　' in text:
        text=text.replace("　　",'　')    
    
    text = re.sub(r'[^\S\n]+', ' ', text)  # Thay thế mọi khoảng trắng (ngoại trừ \n) bằng một dấu cách
    # text = re.sub(r'\s+', ' ', text).replace('\r', ' ').strip()
    text = re.sub(r'(\d),(\d)', r'\1\2', text)
    text = re.sub(r'(\d{4})年(\d{1,2})月(\d{1,2})日', r'\1-\2-\3', text)
    return text

async def translate_text(text,src,dest):
    async with Translator() as translator:
        result = await translator.translate(text,drc=src,dest=dest)
        print(result.text)  # <Translated src=ko dest=en text=Good evening. pronunciation=Good evening.>
    return result.text

def normalize_dict(data):
    """
    Chuẩn hóa toàn bộ dữ liệu dạng dict hoặc list.
    """
    if isinstance(data, dict):
        return {key: normalize_dict(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [normalize_dict(item) for item in data]
    else:
        return normalize_text(data)  # Áp dụng hàm normalize lên giá trị đơn giản

def setupCuda(cuda='0'):
    os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
    os.environ["CUDA_VISIBLE_DEVICES"]=cuda
    os.environ["NCCL_P2P_DISABLE"] = "1"
    os.environ["NCCL_IB_DISABLE"] = "1"

# def extract_json_from_string(text):
#     # Xóa dấu phẩy cuối cùng trong JSON nếu có
#     text = re.sub(r',\s*}', '}', text)
#     text = re.sub(r',\s*\]', ']', text)

#     match = re.search(r'\{[^{}]*\}', text)  # Lấy từ { đầu tiên đến } đầu tiên
#     if match:
#         json_str = match.group(0)  # Chuyển ' thành "
#         try:
#             return json.loads(json_str)  # Parse JSON
#         except json.JSONDecodeError:
#             print("Lỗi: Không thể parse JSON")
#             print(f"json_str ____ {json_str}")
#             return None
#     return None
def extract_json_from_string(text):
    # Xóa dấu phẩy cuối cùng trong JSON nếu có
    text = re.sub(r',\s*}', '}', text)
    text = re.sub(r',\s*\]', ']', text)

    # Lấy từ dấu "{" đầu tiên đến dấu "}" cuối cùng
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        json_str = match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            print("Lỗi: Không thể parse JSON")
            print(f"json_str: {json_str}")
            return None
    return None