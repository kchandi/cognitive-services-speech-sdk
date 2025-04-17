# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from typing import Annotated, Optional
from dotenv import load_dotenv
import io

from azure.identity import AzureCliCredential, get_bearer_token_provider
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from azure.identity import AzureCliCredential
from azure.storage.blob import ContainerClient

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.functions import kernel_function

from video_translation_client import VideoTranslationClient
from video_translation_enum import VoiceKind, WebvttFileKind

load_dotenv()

class VideoTranslationPlugin:
    """A plugin that provides access to video translation capabilities."""
    
    def __init__(self):
        print("Initializing VideoTranslationPlugin...")    
        try:
            credential = AzureCliCredential()
            
            token_provider = get_bearer_token_provider(
                credential, 
                "https://cognitiveservices.azure.com/.default"
            )
            
            self.client = VideoTranslationClient(
                api_version=os.getenv("API_VERSION", "2024-05-20-preview"),
                credential=credential,
                token_provider=token_provider
            )
        except Exception as e:
            print(f"Failed to initialize credential or token provider: {str(e)}")
            # Fall back to default credential
            self.client = VideoTranslationClient(
                api_version=os.getenv("API_VERSION", "2024-05-20-preview")
            )
    
    @kernel_function(description="Translates a video file from source language to target language")
    def translate_video(self, 
                       video_url: Annotated[str, "The URL of the video file to translate"],
                       source_locale: Annotated[str, "The source language code (e.g., en-US, ja-JP)"],
                       target_locale: Annotated[str, "The target language code (e.g., en-US, ja-JP)"],
                       voice_kind: Annotated[str, "The voice type to use: 'PlatformVoice' or 'PersonalVoice'"] = "PlatformVoice",
                       speaker_count: Annotated[Optional[str], "Number of speakers in the video (optional)"] = None,
                       subtitle_max_char_count: Annotated[Optional[str], "Maximum characters per subtitle segment (optional)"] = None,
                       export_subtitle_in_video: Annotated[Optional[bool], "Whether to embed subtitles in video (optional)"] = None
                      ) -> Annotated[str, "Returns the status of the translation request"]:
        """Translates a video from source language to target language."""
        try:

            speaker_count_int = int(speaker_count) if speaker_count else 1
            subtitle_max_char_count_int = int(subtitle_max_char_count) if subtitle_max_char_count else 32

            voice_kind_enum = VoiceKind.PlatformVoice if voice_kind == "PlatformVoice" else VoiceKind.PersonalVoice
            
            success, error, translation, iteration, translation_info, iteration_info = self.client.create_translate_and_run_first_iteration_until_terminated(
                video_file_url=video_url,
                source_locale=source_locale,
                target_locale=target_locale,
                voice_kind=voice_kind_enum,
                speaker_count=speaker_count_int,
                subtitle_max_char_count_per_segment=subtitle_max_char_count_int,
                export_subtitle_in_video=export_subtitle_in_video
            )
            
            if success:
                translation_id = translation.id
                iteration_id = iteration.id
                
                return f"Translation successful! Translation ID:{translation_id} Result translation:{translation_info} Iteration ID:{iteration_id} Result iteration:{iteration_info}"
            else:
                return f"Translation failed: {error}"
        except Exception as e:
            return f"An error occurred during translation: {str(e)}"
            
    @kernel_function(description="Creates an iteration with WebVTT file for an existing translation")
    def create_iteration_with_webvtt(self,
                                    translation_id: Annotated[str, "The ID of the translation to iterate on"],
                                    webvtt_file_url: Annotated[str, "URL of the WebVTT file"],
                                    webvtt_file_kind: Annotated[str, "Kind of WebVTT file: 'MetadataJson', 'SourceLocaleSubtitle', or 'TargetLocaleSubtitle'"],
                                    export_subtitle_in_video: Annotated[Optional[bool], "Whether to embed subtitles in video (optional)"] = None
                                   ) -> Annotated[str, "Returns the status of the iteration creation"]:
        """Creates a new iteration with a WebVTT file for an existing translation."""
        try:
            # Convert string webvtt_file_kind to enum
            webvtt_kind_enum = None
            if webvtt_file_kind == "MetadataJson":
                webvtt_kind_enum = WebvttFileKind.MetadataJson
            elif webvtt_file_kind == "SourceLocaleSubtitle":
                webvtt_kind_enum = WebvttFileKind.SourceLocaleSubtitle
            elif webvtt_file_kind == "TargetLocaleSubtitle":
                webvtt_kind_enum = WebvttFileKind.TargetLocaleSubtitle
            else:
                return f"Invalid WebVTT file kind: {webvtt_file_kind}. Must be 'MetadataJson', 'SourceLocaleSubtitle', or 'TargetLocaleSubtitle'."
                
            success, error, translation, iteration = self.client.run_iteration_with_webvtt_until_terminated(
                translation_id=translation_id,
                webvtt_file_kind=webvtt_kind_enum,
                webvtt_file_url=webvtt_file_url,
                export_subtitle_in_video=export_subtitle_in_video
            )
            
            if success:
                iteration_id = iteration.id
                results = ""
                
                if iteration.result:
                    if iteration.result.translatedVideoFileUrl:
                        results += f"Translated Video: {iteration.result.translatedVideoFileUrl}\n"
                    if iteration.result.sourceLocaleSubtitleWebvttFileUrl:
                        results += f"Source Subtitles: {iteration.result.sourceLocaleSubtitleWebvttFileUrl}\n"
                    if iteration.result.targetLocaleSubtitleWebvttFileUrl:
                        results += f"Target Subtitles: {iteration.result.targetLocaleSubtitleWebvttFileUrl}\n"
                    if iteration.result.metadataJsonWebvttFileUrl:
                        results += f"Metadata: {iteration.result.metadataJsonWebvttFileUrl}\n"
                
                return f"Iteration successfully created! Iteration ID: {iteration_id}\n Translation: {translation} \n Iteration Results:{results}"
            else:
                return f"Iteration creation failed: {error}"
        except Exception as e:
            return f"An error occurred during iteration creation: {str(e)}"

    @kernel_function(description="Lists all translations for the user")
    def list_translations(self) -> Annotated[str, "Returns a list of all translations"]:
        """Lists all translations."""
        try:
            success, error, translations = self.client.request_list_translations()
            
            if success and translations:
                return translations
            else:
                return "Error when retrieving translation list: {error}"
        except Exception as e:
            return f"An error occurred while listing translations: {str(e)}"

    @kernel_function(description="Gets details about a specific translation")
    def get_translation_details(self, translation_id: Annotated[str, "The ID of the translation"]) -> Annotated[str, "Returns details about the specified translation"]:
        """Gets details about a specific translation."""
        try:
            success, error, translation = self.client.request_get_translation(translation_id=translation_id)
            
            if success and translation:
                # result = f"Translation ID: {translation.id}\n"
                # result += f"Status: {translation.status}\n"
                # result += f"Created: {translation.createdDateTime}\n"
                # result += f"Last Action: {translation.lastActionDateTime}\n"
                # result += f"Source: {translation.input.sourceLocale} → Target: {translation.input.targetLocale}\n"
                # result += f"Voice Kind: {translation.input.voiceKind}\n"
                
                # if translation.latestSucceededIteration and translation.latestSucceededIteration.result:
                #     iter_result = translation.latestSucceededIteration.result
                #     result += "\nLatest successful iteration results:\n"
                #     if iter_result.translatedVideoFileUrl:
                #         result += f"Translated Video: {iter_result.translatedVideoFileUrl}\n"
                #     if iter_result.targetLocaleSubtitleWebvttFileUrl:
                #         result += f"Target Subtitles: {iter_result.targetLocaleSubtitleWebvttFileUrl}\n"
                
                return translation
            else:
                return f"Translation not found or error: {error}"
        except Exception as e:
            return f"An error occurred while getting translation details: {str(e)}"
        
    @kernel_function(description="Deletes a specific translation")
    def delete_translation(self, translation_id: Annotated[str, "The ID of the translation to delete"]) -> Annotated[str, "Returns the status of the delete operation"]:
        """Deletes a specific translation."""
        try:
            success, error = self.client.request_delete_translation(translation_id)
            
            if success:
                return f"Translation {translation_id} deleted successfully."
            else:
                return f"Failed to delete translation: {error}"
        except Exception as e:
            return f"An error occurred while deleting the translation: {str(e)}"

    @kernel_function(description="Uploads content to Azure Blob Storage using Managed Identity")
    def upload_to_storage(self, 
                         account_name: Annotated[str, "The storage account name"],
                         container_name: Annotated[str, "The container name"],
                         blob_name: Annotated[str, "The name to give the uploaded blob"],
                         content: Annotated[str, "The text content to upload"]
                        ) -> Annotated[str, "Returns the status of the upload operation"]:
        """Uploads text content to Azure Blob Storage using Managed Identity."""
        try:
            if not self.credential:
                return "No valid credential available for storage access."
            
            container_endpoint = f"https://{account_name}.blob.core.windows.net/{container_name}"
            
            container_client = ContainerClient(
                endpoint=container_endpoint,
                credential=self.credential
            )
            
            try:
                container_client.create_if_not_exists()
                
                content_bytes = content.encode('utf-8')
                
                blob_client = container_client.get_blob_client(blob_name)
                with io.BytesIO(content_bytes) as data:
                    blob_client.upload_blob(data, overwrite=True)
                
                blob_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}"
                
                return f"Successfully uploaded content to blob storage:\nURL: {blob_url}"
            except Exception as e:
                return f"Error during blob upload operation: {str(e)}\n\nThis may indicate that the Managed Identity does not have sufficient RBAC permissions (like Storage Blob Data Contributor) on this storage account."
        except Exception as e:
            return f"Error initializing storage client: {str(e)}"
    
    @kernel_function(description="Downloads content from Azure Blob Storage using Managed Identity")
    def download_from_storage(self,
                             account_name: Annotated[str, "The storage account name"],
                             container_name: Annotated[str, "The container name"],
                             blob_name: Annotated[str, "The name of the blob to download"]
                            ) -> Annotated[str, "Returns the blob content or error message"]:
        """Downloads text content from Azure Blob Storage using Managed Identity."""
        try:
            # Log the storage parameters being used
            print(f"Downloading from storage with parameters:")
            print(f"  Account name: {account_name}")
            print(f"  Container name: {container_name}")
            print(f"  Blob name: {blob_name}")
            
            if not self.credential:
                return "No valid credential available for storage access."
            
            container_endpoint = f"https://{account_name}.blob.core.windows.net/{container_name}"
            
            
            container_client = ContainerClient(
                endpoint=container_endpoint,
                credential=self.credential
            )
            
            try:
                blob_client = container_client.get_blob_client(blob_name)
                
                if not blob_client.exists():
                    return f"Error: Blob '{blob_name}' does not exist in container '{container_name}'."
                
                download_stream = blob_client.download_blob()
                content = download_stream.readall().decode('utf-8')
                
                properties = blob_client.get_blob_properties()
                content_type = properties.content_settings.content_type
                size = properties.size
                
                content_preview = content[:1000] + "..." if len(content) > 1000 else content
                
                return (f"Successfully downloaded blob content using Managed Identity.\n"
                        f"Blob: {blob_name}\n"
                        f"Content Type: {content_type}\n"
                        f"Size: {size} bytes\n\n"
                        f"Content Preview:\n{content_preview}")
            except Exception as e:
                return f"Error downloading blob content: {str(e)}\n\nThis may indicate that the Managed Identity does not have sufficient RBAC permissions (like Storage Blob Data Reader) on this storage account."
        except Exception as e:
             return f"Error initializing storage client: {str(e)}"
        
async def main() -> None:
    ai_agent_settings = AzureAIAgentSettings.create()
    
    print("Starting Video Translation Assistant...")
    print("Type 'exit' or 'quit' to end the conversation.")
    print("-" * 50)

    async with (
        AsyncDefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Create an agent on the Azure AI agent service
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name="Video_Translation_Assistant",
            instructions="""
            You are a helpful video translation assistant. Help users translate their videos from one language to another.
            
            When a user wants to translate a video, gather the necessary information:
            1. The URL of the video
            2. Source language
            3. Target language 
            4. Voice kind (PlatformVoice or PersonalVoice)
            
            After submitting a translation request:
            - Always provide the Translation ID to the user for reference
            - Explain that the translation process takes time to complete
            - Tell users they can check the status of their translation using the ID
            - Share the URLs for the translated video and subtitle files when available
            
            You can also help users:
            - List their translations (It might be helpful to ask if they want to see all translations, a specific number of translations, or translations with a specific criteria)
            - Get details about specific translations
            - Create iterations with WebVTT files
            - Delete translations
            
            Be friendly, helpful, and guide users through the process.
            """,
        )

        # 2. Create a Semantic Kernel agent for the Azure AI agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
            plugins=[VideoTranslationPlugin()],  # Add the video translation plugin
        )

        # 3. Create a thread for the agent
        thread = None

        try:
            print("Video Translation Assistant is ready! How can I help you translate your videos today?")
            
            while True:
                # Get user input from console
                user_input = input("\nYou: ")
                
                # Check for exit commands
                if user_input.lower() in ["exit", "quit"]:
                    print("Ending conversation...")
                    break
                
                print("Assistant is processing...")
                # 4. Invoke the agent for the specified thread for response:
                async for response in agent.invoke(
                    messages=user_input,
                    thread=thread,
                ):
                    # Don't print tool messages, only agent responses
                    #if response.name != "Tool":
                    print(f"\nAssistant: {response}")
                    thread = response.thread
                    
        finally:
            # 5. Cleanup: Delete the thread and agent
            print("\nCleaning up resources...")
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)
            print("Done!")


if __name__ == "__main__":
    asyncio.run(main())