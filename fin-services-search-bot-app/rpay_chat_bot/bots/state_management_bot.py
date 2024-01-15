# from rpay_chat_bot.conversation_data import ConversationData
from botbuilder.core import ActivityHandler, ConversationState, TurnContext, UserState
from botbuilder.schema import ChannelAccount

# from rpay_chat_bot.user_profile import UserProfile
from data_models.user_profile import UserProfile
from data_models.conversation_data import ConversationData
import time
from datetime import datetime
import openai
import sys
from config import DefaultConfig
import json

from botbuilder.schema import HeroCard, CardAction, ActionTypes, CardImage, Attachment, Activity, ActivityTypes
from botbuilder.core import TurnContext, MessageFactory, CardFactory


class StateManagementBot(ActivityHandler):

    def __init__(self, conversation_state: ConversationState, user_state: UserState):
        if conversation_state is None:
            raise TypeError(
                "[StateManagementBot]: Missing parameter. conversation_state is required but None was given"
            )
        if user_state is None:
            raise TypeError(
                "[StateManagementBot]: Missing parameter. user_state is required but None was given"
            )

        self.conversation_state = conversation_state
        self.user_state = user_state
        self.config =  DefaultConfig()

        self.conversation_data_accessor = self.conversation_state.create_property(
            "ConversationData"
        )
        self.user_profile_accessor = self.user_state.create_property("UserProfile")


    async def on_message_activity(self, turn_context: TurnContext):
        # Get the state properties from the turn context.
        user_profile = await self.user_profile_accessor.get(turn_context, UserProfile)
        conversation_data = await self.conversation_data_accessor.get(
            turn_context, ConversationData
        )

        if user_profile.name is None:
            # First time around this is undefined, so we will prompt user for name.
            if conversation_data.prompted_for_user_name:
                # Set the name to what the user provided.
                user_profile.name = turn_context.activity.text

                conversation_data.chat_history = self.init_meta_prompt()

                # Acknowledge that we got their name.
                await turn_context.send_activity(
                    f"Thanks { user_profile.name }. Let me know how can I help you today"
                )

                # Reset the flag to allow the bot to go though the cycle again.
                conversation_data.prompted_for_user_name = False
            else:
                # Prompt the user for their name.
                await turn_context.send_activity("I am your AI Assistant from Razorpay. I can help you quickly get to it! Can you help me with your name?")

                # Set the flag to true, so we don't prompt in the next turn.
                conversation_data.prompted_for_user_name = True
        else:
            # Add message details to the conversation data.
            conversation_data.timestamp = self.__datetime_from_utc_to_local(
                turn_context.activity.timestamp
            )
            conversation_data.channel_id = turn_context.activity.channel_id

            l_chat_history = conversation_data.chat_history
            if l_chat_history is None:
                conversation_data.chat_history = self.init_meta_prompt()
                l_chat_history = conversation_data.chat_history
            
            l_chat_history.append({"role": "user", "content": turn_context.activity.text})

            response_message = openai.ChatCompletion.create(
                engine=self.config.deployment_name, messages=l_chat_history, temperature=0
            )

            llm_response = response_message["choices"][0]["message"]["content"]
            l_chat_history.append({"role": "assistant", "content": llm_response})


            #check if the response is a json
            try:
                json_response = llm_response[
                    llm_response.find("{") : llm_response.rfind("}") + 1
                ]
                if json_response == "":
                    print(llm_response)
                                # Display state data.
                    await turn_context.send_activity(
                        f"{ user_profile.name } : { llm_response }"
                    )
                    # await turn_context.send_activity(
                    #     f"Message received at: { conversation_data.timestamp }"
                    # )
                    # await turn_context.send_activity(
                    #     f"Message received from: { conversation_data.channel_id }"
                    # )
                else:
                    print(
                        "have received the product details to be shown as a card"
                    )
                    resp_object = json.loads(json_response)
                    product_name = resp_object["ProductName"]
                    business_function = resp_object["BusinessFunction"]
                    product_url = resp_object["ProductUrl"]
                    print(product_name, business_function, product_url)
                    card = self.create_hero_card(product_name, business_function, product_url)
                    reply = MessageFactory.attachment(CardFactory.hero_card(card))
                    # attachment = Attachment(content_type=HeroCard.CONTENT_TYPE, content=card.to_dict())
                    # reply = Activity(type=ActivityTypes.message)
                    # reply.text = "Here is the product you are looking for"
                    # reply.attachments = [attachment]
                    # attachment = Attachment(content_type=HeroCard.CONTENT_TYPE, content=card.to_dict())
                    # activity = Activity(type=ActivityTypes.message, attachments=[attachment])
                    # await turn_context.send_activity(MessageFactory.attachment(attachment))
                    await turn_context.send_activity(reply)
                    print("sent the card")
            except:
                pass





    async def on_turn(self, turn_context: TurnContext):
        await super().on_turn(turn_context)

        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    def __datetime_from_utc_to_local(self, utc_datetime):
        now_timestamp = time.time()
        offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(
            now_timestamp
        )
        result = utc_datetime + offset
        return result.strftime("%I:%M:%S %p, %A, %B %d of %Y")
    
    def init_meta_prompt(self) -> any:
        # print("init")
        # read all lines from a text file
        
        with open("metaprompt-1.txt", "r") as file:
            data = file.read().replace("\n", "")
        # print(data)
        chat_history = [{"role": "system", "content": data}]
        return chat_history
    
    def create_hero_card(self, product_name, business_function, product_url) -> HeroCard:
        card = HeroCard(
            title=product_name,
            subtitle=product_name,
            text=business_function,
            images=[CardImage(url="https://marketplace.cs-cart.com/images/thumbnails/700/280/detailed/4/logo_black.png")],
            buttons=[
                CardAction(type=ActionTypes.open_url, title="Launch Product Page", value=product_url)
            ]
        )
        return card