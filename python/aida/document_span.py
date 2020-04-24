"""
AIDA DocumentSpan class.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "10 February 2020"

from aida.object import Object
from aida.span import Span
from aida.utility import get_md5_from_string

def normalize_span_type(span_type):
    normalized_span_types = {
        'picture':  'picture_channel_video',
        'sound':    'sound_channel_video',
        'both':     'both_channel_video'
        }
    return normalized_span_types[span_type] if span_type in normalized_span_types else span_type

class DocumentSpan(Object):
    """
    AIDA DocumentSpan class to be used for storing a text span, or
    an image or video bounding box including document_id, document_element_id and keyframe_id
    """
    
    valid_span_types = ['text', 'image', 'keyframe', 'picture_channel_video', 'sound_channel_video', 'both_channels_video', 'audio']

    def __init__(self, logger, document_id, document_element_id, keyframe_id, document_element_modality, span_type, start_x, start_y, end_x, end_y, where):
        """
        Initialize the DocumentSpan object.
        
        Arguments:
            logger (aida.Logger):
                the aida.Logger object
            document_id (string):
                identifier of the document
            document_element_id (string):
                identifier of the document element
            keyframe_id (string, or None):
                identifier of the keyframe; None if not applicable
            document_element_modality (string):
                modality of the document element
            span_type (string):
                type of the span; options: text, image, keyframe, picture, sound, audio
                    text:
                        span has start (start_x) and end (end_x) offset from a text document element;
                        [start|end]_y are both zero
                    image:
                        span has a bounding box from an image
                    keyframe:
                        span has a bounding box from a keyframe
                    picture:
                        mention is in the picture channel of a video document element;
                        span has start (start_x) and end (end_x) time from the video;
                        [start|end]_y are both zero
                    sound:
                        mention is in the sound channel of a video document element;
                        span has start (start_x) and end (end_x) time from the video;
                        [start|end]_y are both zero
                    audio:
                        span has start (start_x) and end (end_x) time from an audio document element;
                        [start|end]_y are both zero
            start_x (string):
                the start character position of a text document, or
                the top-left-x coordinate for an image
            start_y (string):
                zero ('0') for a text document, or
                the top-left-y coordinate for an image
            end_x (string):
                the end character position of a text document, or
                the bottom-right-x coordinate for an image
            end_y (string):
                zero ('0') for a text document, or
                the bottom-right-y coordinate for an image
            where:
                a dictionary containing values corresponding to the following two keys used to store
                information about the filename and line number where the span (as represented by the
                current instance of DocumentSpan) was found:
                    filename
                    lineno
                Primarily used for recording any logging information.
        """
        super().__init__(logger)
        self.document_id = document_id
        self.document_element_id = document_element_id
        self.keyframe_id = keyframe_id
        self.document_element_modality = document_element_modality
        self.span_type = normalize_span_type(span_type)
        if self.span_type not in self.valid_span_types:
            self.logger.record_event('UNEXPECTED_SPAN_TYPE', ','.join(self.valid_span_types), span_type, where)
        self.span = Span(logger, start_x, start_y, end_x, end_y)
    
    def get_md5(self):
        """
            Gets the MD5 sum corresponding to the string representation of the span represented by the
            current instance of DocumentSpan.
        """
        return get_md5_from_string(self.__str__())

    def __str__(self, *args, **kwargs):
        """
        Return a string containing the bounding box in the form:
            DOCUMENT_ID:DOCUMENT_ELEMENT_ID:START-END
        where
            START=(start_x,start_y)
            END=(end_x,end_y)
        """
        span_text = ''
        if self.get('keyframe_id') is None:
            span_text = "{}:{}:{}".format(self.get('document_id'), 
                                    self.get('document_element_id'), 
                                    self.get('span'))
        else:
            span_text = "{}:{}:{}".format(self.get('document_id'), 
                                    self.get('keyframe_id'), 
                                    self.get('span'))
        return span_text