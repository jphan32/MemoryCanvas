import gradio as gr
import base64
import uuid
import shutil

import os
import requests
from openai import OpenAI

client = OpenAI()

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY')}"
}


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def draw_image(class_value, name_value, text_value, image_path, images):
    if not class_value or not name_value:
        gr.Warning("학년 반 번호와 이름을 입력해주세요.", duration=5)
        return None, images

    if not text_value:
        gr.Warning("어떤 그림을 그릴지 인공지능에게 설명해주세요.", duration=5)
        return None, images

    # Generate prompt for the drawing image generation
    if image_path:
        base64_image = encode_image(image_path)

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Describe the attached image in text, translate the user's input into English, and combine them into a prompt for DALL-E to generate an image.
Print ONLY the combined prompt as a string.

Example:
```
1. Image description: **attached image**
2. User input (in English): 배경 그림에 산을 추가해줘.
3. Combined prompt: A red lighthouse standing against the backdrop of the sea under a blue sky. Please add mountains in the background.
```
```
1. Image description: **attached image**
2. User input (in English): 하늘을 나는 미래형 비행 자동차를 그려줘.
3. Combined prompt: A busy city street at night with bright neon signs and a crowd of people walking. Please add a futuristic flying car in the sky.
```
===

User input:
1. Image description: **attached image**
2. User input (in English): {text_value}.
3. Combined prompt: """
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 2000
        }

        json = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload).json()
        # print(json["choices"][0]["message"]["content"])
        text_value = json["choices"][0]["message"]["content"]

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=text_value,
            size="1024x1024",
            quality="hd",
            n=1,
        )
    except Exception as e:
        gr.Warning("인공지능에게 전달한 문장을 다시 한 번 확인해보세요.", duration=5)
        return None, images

    image_url = response.data[0].url
    drawing_image = gr.Image(image_url, interactive=False)

    # Update image gallery
    if not images:
        images = [image_url]
    else:
        images.append(image_url)

    return drawing_image, images


def get_select_index(evt: gr.SelectData):
    return evt.index


def save_image(images, selected_index, class_value, name_value):
    if not images or not class_value or not name_value:
        gr.Error("저장할 이미지가 없거나 이름을 입력하지 않았습니다.", duration=5)
        return

    if selected_index == -1:
        gr.Warning("이미지를 선택하지 않았습니다.", duration=5)
        return

    print(images, selected_index)
    for img in images:
        unique_filename = f"./work/{class_value}_{name_value}_{uuid.uuid4()}.png"
        print(img[0], unique_filename)
        shutil.copy2(img[0], unique_filename)

    if selected_index is not None:
        shutil.copy2(images[selected_index][0], f"./work/{class_value}_{name_value}_Selected.png")

    gr.Info("선택한 이미지를 저장했습니다.", duration=5)


with gr.Blocks() as demo:
    gr.Markdown("# ✨ 인공지능과 함께 그리는 우리 마을 이야기 🏞️")

    gr.Markdown("## 누가 그릴까요? 👩‍🎨")
    with gr.Row():
        with gr.Column():
            class_input = gr.Textbox(label="학년 반 번호", lines=1, placeholder="예) 6101")
        with gr.Column():
            name_input = gr.Textbox(label="이름", lines=1)

    gr.Markdown("## 어떤 그림을 그릴까요? 🎨")
    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(label="인공지능에게 전달할 문장을 입력해주세요.", lines=10,
                                    placeholder="예) 만화 캐릭터 고양이를 수채화 느낌으로 그려줘.")
        with gr.Column():
            image_input = gr.Image(label="인공지능에게 전달할 이미지를 업로드 해주세요.", type="filepath")
    with gr.Row():
        draw_button = gr.Button("그림 그리기")

    gr.Markdown("---")
    gr.Markdown("## 그림 결과물 🖼️")
    with gr.Row():
        processed_image = gr.Image(label="그림 결과물", interactive=False)

    with gr.Row():
        image_gallery = gr.Gallery(label="지금까지 그린 그림들", columns=8, interactive=False)
        selected = gr.Number(value=-1, show_label=False, visible=False)

    save_button = gr.Button("선택한 이미지 저장하기")

    # Event Handlers
    draw_button.click(draw_image,
                      inputs=[class_input, name_input, text_input, image_input, image_gallery],
                      outputs=[processed_image, image_gallery])
    image_gallery.select(get_select_index, None, selected)
    save_button.click(save_image, inputs=[image_gallery, selected, class_input, name_input], outputs=[])

if __name__ == "__main__":
    demo.queue().launch(share=False, debug=True)
