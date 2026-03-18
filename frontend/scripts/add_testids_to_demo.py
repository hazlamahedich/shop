#!/usr/bin/env python3
"""
Add data-testid attributes to WidgetDemo.tsx demo components for E2E testing.
"""

import re
from pathlib import Path


def add_testids_to_demo():
    file_path = Path("frontend/src/widget/demo/WidgetDemo.tsx")

    with open(file_path, "r") as f:
        content = f.read()

    replacements = []

    # Find all demo components and their positions
    demo_ranges = {
        "GlassmorphismDemo": None,
        "CarouselDemo": None,
        "QuickReplyDemo": None,
        "VoiceInputDemo": None,
        "ProactiveDemo": None,
        "GroupingDemo": None,
        "AnimationsDemo": None,
        "PositioningDemo": None,
    }

    # Pattern to find chat bubble buttons in each demo
    # Look for buttons with position: 'fixed' and bottom: '20px'

    # Define patterns and replacements for each component type
    patterns = [
        # GlassmorphismDemo - Chat Bubble (first occurrence after function definition)
        # Find the button that has onClick={() => setIsOpen(!isOpen)}
        (
            r"(function GlassmorphismDemo[^{]*\{[\s\S]*?<button\s+onClick=\{\(\) => setIsOpen\(!isOpen)\})",
            r'\1\n        data-testid="chat-bubble"',
        ),
        # GlassmorphismDemo - Chat Window
        (
            r"(\{isOpen && \(\s*<div\s+style=\{\{[\s\S]*?position: \'fixed\',[\s\S]*?bottom: \'90px\')",
            r'\1 data-testid="chat-window"',
        ),
        # GlassmorphismDemo - Message Input
        (
            r'(<input\s+type="text"\s+placeholder="Type a message\.\.\.")',
            r'\1 data-testid="message-input"',
        ),
        # GlassmorphismDemo - Send Button
        (r"(>Send\s*</button>)", r' data-testid="send-message-button"\1'),
    ]

    # Since the file is complex, let's use a different approach
    # Find specific sections and add data-testid attributes

    lines = content.split("\n")
    modified_lines = []

    in_glassmorphism = False
    in_carousel = False
    in_quickreply = False
    in_voice = False
    in_proactive = False
    in_grouping = False
    in_animations = False
    in_positioning = False

    chat_bubble_added = {
        "glassmorphism": False,
        "carousel": False,
        "quickreply": False,
        "voice": False,
        "proactive": False,
        "grouping": False,
        "animations": False,
        "positioning": False,
    }
    chat_window_added = {
        "glassmorphism": False,
        "carousel": False,
        "quickreply": False,
        "voice": False,
        "grouping": False,
        "animations": False,
    }
    input_added = {
        "glassmorphism": False,
        "carousel": False,
        "quickreply": False,
        "voice": False,
        "grouping": False,
        "animations": False,
    }
    send_button_added = {
        "glassmorphism": False,
        "carousel": False,
        "quickreply": False,
        "voice": False,
        "grouping": False,
        "animations": False,
    }
    voice_button_added = False
    carousel_container_added = False
    proactive_modal_added = False

    for i, line in enumerate(lines):
        # Track which demo we're in
        if "function GlassmorphismDemo" in line:
            in_glassmorphism = True
            in_carousel = False
            in_quickreply = False
            in_voice = False
            in_proactive = False
            in_grouping = False
            in_animations = False
            in_positioning = False
        elif "function CarouselDemo" in line:
            in_glassmorphism = False
            in_carousel = True
            in_quickreply = False
            in_voice = False
            in_proactive = False
            in_grouping = False
            in_animations = False
            in_positioning = False
        elif "function QuickReplyDemo" in line:
            in_glassmorphism = False
            in_carousel = False
            in_quickreply = True
            in_voice = False
            in_proactive = False
            in_grouping = False
            in_animations = False
            in_positioning = False
        elif "function VoiceInputDemo" in line:
            in_glassmorphism = False
            in_carousel = False
            in_quickreply = False
            in_voice = True
            in_proactive = False
            in_grouping = False
            in_animations = False
            in_positioning = False
        elif "function ProactiveDemo" in line:
            in_glassmorphism = False
            in_carousel = False
            in_quickreply = False
            in_voice = False
            in_proactive = True
            in_grouping = False
            in_animations = False
            in_positioning = False
        elif "function GroupingDemo" in line:
            in_glassmorphism = False
            in_carousel = False
            in_quickreply = False
            in_voice = False
            in_proactive = False
            in_grouping = True
            in_animations = False
            in_positioning = False
        elif "function AnimationsDemo" in line:
            in_glassmorphism = False
            in_carousel = False
            in_quickreply = False
            in_voice = False
            in_proactive = False
            in_grouping = False
            in_animations = True
            in_positioning = False
        elif "function PositioningDemo" in line:
            in_glassmorphism = False
            in_carousel = False
            in_quickreply = False
            in_voice = False
            in_proactive = False
            in_grouping = False
            in_animations = False
            in_positioning = True

        # Add data-testid to chat bubble buttons
        if "<button" in line and "position: 'fixed'" in line and "bottom: '20px'" in line:
            if in_glassmorphism and not chat_bubble_added["glassmorphism"]:
                line = line.replace("<button", '<button data-testid="chat-bubble"')
                chat_bubble_added["glassmorphism"] = True
            elif in_carousel and not chat_bubble_added["carousel"]:
                line = line.replace("<button", '<button data-testid="chat-bubble"')
                chat_bubble_added["carousel"] = True
            elif in_quickreply and not chat_bubble_added["quickreply"]:
                line = line.replace("<button", '<button data-testid="chat-bubble"')
                chat_bubble_added["quickreply"] = True
            elif in_voice and not chat_bubble_added["voice"]:
                line = line.replace("<button", '<button data-testid="chat-bubble"')
                chat_bubble_added["voice"] = True
            elif in_proactive and not chat_bubble_added["proactive"]:
                line = line.replace("<button", '<button data-testid="chat-bubble"')
                chat_bubble_added["proactive"] = True
            elif in_grouping and not chat_bubble_added["grouping"]:
                line = line.replace("<button", '<button data-testid="chat-bubble"')
                chat_bubble_added["grouping"] = True
            elif in_animations and not chat_bubble_added["animations"]:
                line = line.replace("<button", '<button data-testid="chat-bubble"')
                chat_bubble_added["animations"] = True
            elif in_positioning and not chat_bubble_added["positioning"]:
                line = line.replace("<button", '<button data-testid="chat-bubble"')
                chat_bubble_added["positioning"] = True

        # Add data-testid to chat window divs
        if "<div" in line and "position: 'fixed'" in line and "bottom: '90px'" in line:
            if in_glassmorphism and not chat_window_added["glassmorphism"]:
                line = line.replace("<div", '<div data-testid="chat-window"')
                chat_window_added["glassmorphism"] = True
            elif in_carousel and not chat_window_added["carousel"]:
                line = line.replace("<div", '<div data-testid="chat-window"')
                chat_window_added["carousel"] = True
            elif in_quickreply and not chat_window_added["quickreply"]:
                line = line.replace("<div", '<div data-testid="chat-window"')
                chat_window_added["quickreply"] = True
            elif in_voice and not chat_window_added["voice"]:
                line = line.replace("<div", '<div data-testid="chat-window"')
                chat_window_added["voice"] = True
            elif in_grouping and not chat_window_added["grouping"]:
                line = line.replace("<div", '<div data-testid="chat-window"')
                chat_window_added["grouping"] = True
            elif in_animations and not chat_window_added["animations"]:
                line = line.replace("<div", '<div data-testid="chat-window"')
                chat_window_added["animations"] = True

        # Add data-testid to message inputs
        if "<input" in line and 'type="text"' in line and 'placeholder="Type a message' in line:
            if in_glassmorphism and not input_added["glassmorphism"]:
                line = line.replace("<input", '<input data-testid="message-input"')
                input_added["glassmorphism"] = True
            elif in_carousel and not input_added["carousel"]:
                line = line.replace("<input", '<input data-testid="message-input"')
                input_added["carousel"] = True
            elif in_grouping and not input_added["grouping"]:
                line = line.replace("<input", '<input data-testid="message-input"')
                input_added["grouping"] = True

        # Add data-testid to voice input placeholder
        if "<input" in line and 'placeholder="Type or use voice' in line:
            if in_voice and not input_added["voice"]:
                line = line.replace("<input", '<input data-testid="message-input"')
                input_added["voice"] = True

        # Add data-testid to quick reply placeholder
        if "<input" in line and 'placeholder="Type a message' in line:
            if in_quickreply and not input_added["quickreply"]:
                line = line.replace("<input", '<input data-testid="message-input"')
                input_added["quickreply"] = True

        # Add data-testid to animations placeholder
        if "<input" in line and 'placeholder="Type a message' in line:
            if in_animations and not input_added["animations"]:
                line = line.replace("<input", '<input data-testid="message-input"')
                input_added["animations"] = True

        # Add data-testid to send buttons (after message input in same component)
        # Look for Send buttons
        if ">Send</button>" in line:
            if in_glassmorphism and not send_button_added["glassmorphism"]:
                line = line.replace(
                    ">Send</button>", ' data-testid="send-message-button">Send</button>'
                )
                send_button_added["glassmorphism"] = True
            elif in_carousel and not send_button_added["carousel"]:
                line = line.replace(
                    ">Send</button>", ' data-testid="send-message-button">Send</button>'
                )
                send_button_added["carousel"] = True
            elif in_voice and not send_button_added["voice"]:
                line = line.replace(
                    ">Send</button>", ' data-testid="send-message-button">Send</button>'
                )
                send_button_added["voice"] = True
            elif in_grouping and not send_button_added["grouping"]:
                line = line.replace(
                    ">Send</button>", ' data-testid="send-message-button">Send</button>'
                )
                send_button_added["grouping"] = True
            elif in_animations and not send_button_added["animations"]:
                line = line.replace(
                    ">Send</button>", ' data-testid="send-message-button">Send</button>'
                )
                send_button_added["animations"] = True

        # Add data-testid to voice input button
        if "onClick={startListening}" in line and "<button" in lines[i - 1] if i > 0 else False:
            if in_voice and not voice_button_added:
                # Modify the previous line (button opening tag)
                modified_lines[-1] = modified_lines[-1].replace(
                    "<button", '<button data-testid="voice-input-button"'
                )
                voice_button_added = True

        # Add data-testid to carousel container
        if in_carousel and "overflowX: 'auto'" in line and not carousel_container_added:
            # This is the carousel scroll container
            # Find the div that contains this
            if "<div" in line:
                line = line.replace("<div", '<div data-testid="product-carousel"')
                carousel_container_added = True

        # Add data-testid to quick reply buttons
        if in_quickreply and "{quickReplies.map((reply)" in line:
            # The next button should have the testid
            pass

        # Add data-testid to quick reply button (look for key={reply.id})
        if "key={reply.id}" in line and in_quickreply:
            # The button should be on the next line or same line
            if "<button" in line:
                line = line.replace(
                    "<button", '<button data-testid="quick-reply-button-{reply.id}"'
                )

        # Add data-testid to proactive modal
        if in_proactive and "showPopup && (" in line:
            # Next div should be the modal
            pass

        if in_proactive and "{showPopup && (" in line:
            # Check if next line has a div
            if i + 1 < len(lines) and "<div" in lines[i + 1]:
                modified_lines.append(line)
                modified_lines[-1] = lines[i + 1].replace(
                    "<div", '<div data-testid="proactive-modal"'
                )
                continue

        # Add data-testid to proactive engage button
        if in_proactive and "{currentMessage.cta}" in line:
            if "<button" in line:
                line = line.replace("<button", '<button data-testid="proactive-engage-button"')

        # Add to cart buttons in carousel
        if in_carousel and "onClick={() => handleAddToCart(product.id)}" in line:
            if "<button" in line:
                line = line.replace("<button", '<button data-testid="add-to-cart-button"')

        modified_lines.append(line)

    content = "\n".join(modified_lines)

    with open(file_path, "w") as f:
        f.write(content)

    print("Added data-testid attributes to WidgetDemo.tsx")


if __name__ == "__main__":
    add_testids_to_demo()
