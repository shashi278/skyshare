from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.anchorlayout import AnchorLayout
from kivy.logger import Logger
from kivy.lang.builder import Builder
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
)
from kivy.uix.behaviors import ButtonBehavior
from kivy.animation import Animation
from kivy.clock import Clock, mainthread
from kivy.uix.recycleview.views import _clean_cache
from kivy.uix.screenmanager import SlideTransition

from kivyauth.google_auth import initialize_google, login_google, logout_google
from kivyauth.facebook_auth import initialize_fb, login_facebook, logout_facebook
from kivyauth.providers import login_providers

from jnius import autoclass, cast, JavaException
from android import python_act
from android.activity import bind as result_bind
from android.permissions import request_permissions, Permission, check_permission, PERMISSION_GRANTED
from android.runnable import run_on_ui_thread

from kivymd.app import MDApp
from kivymd.uix.button import RectangularElevationBehavior, MDRectangleFlatIconButton
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import RectangularRippleBehavior
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog

import threading
import certifi
import siaskynet
import os
import time

os.environ['SSL_CERT_FILE']= certifi.where()

Intent= autoclass("android.content.Intent")

Activity= autoclass("android.app.Activity")
MediaStore= autoclass("android.provider.MediaStore$Images$Media")
Context= autoclass("android.content.Context")
Uri= autoclass("android.net.Uri")
CharSequence= autoclass('java.lang.CharSequence')
String = autoclass('java.lang.String')
Toast= autoclass('android.widget.Toast')
LayoutParams= autoclass('android.view.WindowManager$LayoutParams')
AndroidColor= autoclass('android.graphics.Color')

PICK_IMAGE=1019
RC_SIGN_IN=2029
context= python_act.mActivity
#Logger.info("Hahaha: {}".format(help(siaskynet)))
skynet= siaskynet
app_directory= "/storage/emulated/0/SkyShare"
download_directory= app_directory+"/downloads"

kv="""
ScreenManager:

    LoginScreen:
        id: login_screen

    UploadScreen:
        id: upload_screen

    

    

    DownloadScreen:
        id: download_screen
    

<LoginScreen@Screen>:
    name:"loginscreen"

    canvas:
        Color:
            rgba: 1,1,1,.3
        Rectangle:
            pos: self.x, max(root.width, root.height)/2 - min(root.width, root.height)/2
            size: min(root.width, root.height), min(root.width, root.height)
            source: "skynet_logo_big.png"

    BoxLayout:
        pos_hint: {"center_x":.5, "center_y":.5}
        orientation:"vertical"

        BoxLayout:
            size_hint_y: None
            height: self.minimum_height
            MDToolbar:
                title:"SkyShare"
                elevation: 10
                right_action_items: [["information-outline", lambda x: None]]
        
        BoxLayout:
            size_hint_y: None
            height: self.minimum_height+dp(50)
            padding: 0,dp(60),0,0
            MDLabel:
                text: "Continue SkyShare with"
                halign:"center"
                bold:True
                theme_text_color:"Custom"
                text_color: .2,.2,.2,.7
        
        BoxLayout:
            orientation:"vertical"

            LoginButton:
                text: "Google"
                icon: "google"
                text_color: 1,1,1,1
                can_color: 66/255, 133/255, 244/255, 1
                release_action: app.gl_login
            
            LoginButton:
                text: "Facebook"
                icon: "facebook-box"
                text_color: 1,1,1,1
                can_color: 59/255, 89/255, 152/255, 1
                release_action: app.fb_login
        
        BoxLayout:
            size_hint_y: None
            height: self.minimum_height+dp(50)
            MDLabel:
                text:"---or---"
                halign: "center"
                bold:True
                theme_text_color:"Custom"
                text_color: .2,.2,.2,.7
        BoxLayout:
            size_hint_y:None
            height: self.minimum_height+dp(50)
            padding: 0,dp(30),0,0
            LoginButton:
                text: "As Guest"
                icon: "account-circle"
                text_color: 1,1,1,1
                can_color: app.theme_cls.primary_color
                release_action: app.guest_login

        
        Widget:
        
<LoginButton@AnchorLayout>:
    text:""
    icon: ""
    text_color: [0,0,0,1]
    can_color: 1,1,1,1
    release_action: print
    RectangleRaisedIconButton:
        elevation:8
        width: dp(150)
        height: dp(50)
        canvas.before:
            Color:
                rgba: root.can_color
            Rectangle:
                pos: self.pos
                size: self.size
        
        icon: root.icon
        text: root.text
        font_size: dp(8)
        text_color: root.text_color
        halign: "center"
        on_release:
            if root.release_action: root.release_action()
        
<UploadScreen@Screen>:
    name:"upload_screen"
    
    BoxLayout:
        pos_hint: {"center_x":.5, "center_y":.5}
        orientation: "vertical"

        MDToolbar:
            title: "Upload Images"
            elevation: 10
            left_action_items: [["menu", lambda x: None]]
            right_action_items: [["download", lambda x: app.change_screen('download_screen')],["plus", lambda x: app.add_image()]]
        

        # RecycleView:
        #     id:rv
        #     viewclass: 'SmartTiles'
        #     #data: [{'source':"https://i.ibb.co/cbQQcmz/chat.png"}]
        #     #     {'source':"/storage/emulated/0/DCIM/Camera/IMG_20200722_114758.jpg"},\
        #     #     {'source': "/storage/emulated/0/DCIM/Camera/IMG_20200722_115751.jpg"},\
        #     #     {'source': "/storage/emulated/0/DCIM/Camera/IMG_20200722_114758.jpg"}\
        #     #     ]

        #     RecycleGridLayout:
        #         default_size: None, (root.width-dp(16))/3
        #         default_size_hint: 1, None
        #         size_hint_y: None
        #         height: self.minimum_height
        #         cols: 3
        #         padding: dp(4), dp(4)
        #         spacing: dp(4)
        
        ScrollView:

            MDGridLayout:
                id: grid
                cols: 2
                adaptive_height: True
                padding: dp(4), dp(4)
                spacing: dp(4)

<DownloadScreen@Screen>:
    name:"download_screen"
    on_enter:
        app.create_download_directory()
    
    BoxLayout:
        pos_hint: {"center_x":.5, "center_y":.5}
        orientation: "vertical"

        MDToolbar:
            title: "Download Images"
            elevation: 10
            left_action_items: [["menu", lambda x: None]]
            right_action_items: [["upload", lambda x: app.change_screen('upload_screen')], ["plus", lambda x: app.show_link_popup()]]
        
        ScrollView:

            MDGridLayout:
                id: grid
                cols: 2
                adaptive_height: True
                padding: dp(4), dp(4)
                spacing: dp(4)


<SmartTiles>
    _img_widget: img
    _img_overlay: img_overlay
    _box_overlay: box
    tile_no: 0
    size_hint_y: None
    height: self.width
    on_release:
        app.tiles_touched(self) if root.upload_done else None

    FitImage:
        id: img
        source: root.source
        x: root.x
        y: root.y if root.overlap or root.box_position == 'header' else box.top

    BoxLayout:
        id: img_overlay
        size_hint: img.size_hint
        size: img.size
        pos: img.pos

    MDFloatLayout:
        orientation: "vertical"
        id: box
        md_bg_color: [0,0,0, root.box_color_alpha]
        x: root.x
        y: root.y
        BoxLayout:
            pos_hint: {"center_x":.5, "center_y":root.box_y}
            opacity: root.box_opacity
            AnchorLayout:
                MDIconButton:
                    icon: "delete"
                    theme_text_color: "Custom"
                    text_color: 1,1,1,1
                    user_font_size: "20sp"
            
            BoxLayout:
                AnchorLayout:
                    MDIconButton:
                        icon: "share"
                        theme_text_color: "Custom"
                        text_color: 1,1,1,1
                        user_font_size: "25sp"
                        on_release:
                            app.share_skylink(root)

    MDFloatLayout:
        orientation: "vertical"
        id: spinner_box
        md_bg_color: [0,0,0, root.spinner_box_alpha]
        x: root.x
        y: root.y
        MDSpinner:
            id: spinner
            size_hint: None, None
            size: dp(46), dp(46)
            pos_hint: {'center_x': .5, 'center_y': .5}
            active: root.spinner_active
        
        MDLabel:
            text:root.spinner_text
            font_style:"Caption"
            halign: "center"
            pos_hint: {'center_x': .5, 'center_y': .15}
            theme_text_color: "Custom"
            text_color: 1, 1, 1, .8

<Content>:
    size_hint_y: None
    height: "70dp"

    MDTextField:
        id:link
        hint_text: "Skylink"

"""

def get_permission():
    if not check_permission(Permission.WRITE_EXTERNAL_STORAGE):
        request_permissions([Permission.WRITE_EXTERNAL_STORAGE])

get_permission()

@run_on_ui_thread
def show_toast(text):
    t= Toast.makeText(context, cast(CharSequence, String(text)), Toast.LENGTH_SHORT)
    t.show()

@run_on_ui_thread
def set_statusbar_color(color):
    window= context.getWindow()
    window.addFlags(LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS)
    window.setStatusBarColor(AndroidColor.parseColor(color))

def get_file_path(uri):
    filePath=""
    try:
        cursor = context.getContentResolver().query(uri, None, None, None, None)
        if cursor.moveToFirst():
            column_index = cursor.getColumnIndexOrThrow("_data")
            filePathUri = Uri.parse(cursor.getString(column_index))
            filePath= filePathUri.getPath()
            Logger.info("Hahaha: filePath={}".format(filePath))
            cursor.close()
    except JavaException:
        Logger.info("Hahaha: _data wala error")
        filePath= "/storage/emulated/0/"+Uri.parse(uri.toString()).getPath().split(":")[-1]
    
    if not filePath:
        return None
    return filePath


class RectangleRaisedIconButton(MDRectangleFlatIconButton, RectangularElevationBehavior):
    elevation_normal=16

class SmartTiles(
    ThemableBehavior, ButtonBehavior, MDFloatLayout
):
    """
    A tile for more complex needs.
    Includes an image, a container to place overlays and a box that can act
    as a header or a footer, as described in the Material Design specs.
    """

    box_color_alpha = NumericProperty(0)
    spinner_box_alpha= NumericProperty(0.4)
    """
    Sets the color and opacity for the information box.
    :attr:`box_color` is a :class:`~kivy.properties.ListProperty`
    and defaults to `(0, 0, 0, 0.5)`.
    """

    box_position = OptionProperty("footer", options=["footer", "header"])
    """
    Determines wether the information box acts as a header or footer to the
    image. Available are options: `'footer'`, `'header'`.
    :attr:`box_position` is a :class:`~kivy.properties.OptionProperty`
    and defaults to `'footer'`.
    """

    lines = OptionProperty(1, options=[1, 2])
    """
    Number of lines in the `header/footer`. As per `Material Design specs`,
    only 1 and 2 are valid values. Available are options: ``1``, ``2``.
    :attr:`lines` is a :class:`~kivy.properties.OptionProperty`
    and defaults to `1`.
    """

    overlap = BooleanProperty(True)
    spinner_active= BooleanProperty(True)
    """
    Determines if the `header/footer` overlaps on top of the image or not.
    :attr:`overlap` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to `True`.
    """

    source = StringProperty()
    """
    Path to tile image. See :attr:`~kivy.uix.image.Image.source`.
    :attr:`source` is a :class:`~kivy.properties.StringProperty`
    and defaults to `''`.
    """

    box_y= NumericProperty(-.3)

    box_opacity= NumericProperty(0)

    upload_done= BooleanProperty(False)

    skylink= StringProperty()

    spinner_text= StringProperty("Uploading...")

    _img_widget = ObjectProperty()
    _img_overlay = ObjectProperty()
    _box_overlay = ObjectProperty()
    _box_label = ObjectProperty()

    def reload(self):
        self._img_widget.reload()

class Content(AnchorLayout):
    pass

class SaveImageApp(MDApp):
    current_provider=""
    previous_tile_inst= ObjectProperty()
    selected_images=[]
    dialog= None
    def build(self):
        if not os.path.exists(app_directory):
            os.makedirs(app_directory)
        initialize_google(self.after_login, self.error_listener)
        initialize_fb(self.after_login, self.cancel_listener, self.error_listener)
        
        self.theme_cls.primary_palette = "Green"
        return Builder.load_string(kv)
    
    def on_resume(self, *args):
        #super().on_resume()
        return True

    def on_start(self):
        primary_clr= self.theme_cls.primary_dark
        hex_color= '#%02x%02x%02x' % (int(primary_clr[0]*255), int(primary_clr[1]*255), int(primary_clr[2]*255))
        set_statusbar_color(hex_color)
    
    def change_screen(self, scrn_name):
        if scrn_name=="download_screen":
            self.root.transition= SlideTransition(direction="down")
            Logger.info("Hahaha: heererereererererereere")
        else:
            self.root.transition= SlideTransition(direction="up")

        self.root.current= scrn_name
        self.root.transition= SlideTransition(direction="right")
    
    def fb_login(self, *args):
        login_facebook()
        self.current_provider= login_providers.facebook
        
    def gl_login(self, *args):
        # Logger.info("Hahaha: Cannot login google")
        # show_toast("Logging in using google")
        login_google()
        self.current_provider= login_providers.google
    
    def guest_login(self):
        # Logger.info("Hahaha: Cannot login")
        # show_toast("Logging in as guest")
        self.root.current= "upload_screen"

    def open_gallery(self, *args):
        self.selected_images=[]
        gallery = Intent()
        gallery.setType("image/*")
        gallery.setAction(Intent.ACTION_GET_CONTENT)
        #gallery.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, True)
        result_bind(on_activity_result=self.activity_result_gallery)
        context.startActivityForResult(gallery, PICK_IMAGE)
    
    def activity_result_gallery(self, request_code, result_code, data):
        if request_code==PICK_IMAGE and result_code==Activity.RESULT_OK:
            #grid= self.root.ids.upload_screen.ids.grid
            uri = data.getData()
            mClipData = data.getClipData()
            if uri:
                Logger.info("Hahaha: uri={}".format(uri))
                file_path= get_file_path(uri)
                Logger.info("Hahaha: uri_path={}".format(file_path))
                if file_path not in self.selected_images:
                        
                    t = threading.Thread(
                        target=self.upload_images, args=(file_path,)
                    )
                    t.start()
                    self.selected_images.append(file_path)

            elif mClipData:
                Logger.info("Hahaha: mClip={}".format(mClipData))
                
                for i in range(mClipData.getItemCount()):
                    item = mClipData.getItemAt(i)
                    uri = item.getUri()
                    file_path= get_file_path(uri)
                    Logger.info("Hahaha: mClipUri_{}_path={}".format(i, file_path))
                    if file_path not in self.selected_images:
                        
                        t = threading.Thread(
                            target=self.upload_images, args=(file_path, )
                        )
                        t.start()
                        self.selected_images.append(file_path)
                
        else:
            Logger.info("Hahaha: Cancelled")
    
    def logout_(self):
        if self.current_provider==login_providers.google:
            logout_google(self.after_logout)
        if self.current_provider==login_providers.facebook:
            logout_facebook(self.after_logout)
        else:
            self.root.current= "loginscreen"

    def after_login(self, name, email, photo_uri):
        #show_toast('Logged in using {}'.format(current_provider))
        self.root.current= 'upload_screen'
        self.update_ui(name, email, photo_uri)

    def after_logout(self):
        self.update_ui('','','')
        self.root.current= 'loginscreen'
        #show_toast('Logged out from {} login'.format(current_provider))
    
    def update_ui(self, name, email, photo_uri):
        pass
        #self.root.ids.upload_screen.ids.user_name.title= name
        #self.root.ids.upload_screen.ids.user_email.text= "Your Email: {}".format(email)
    
    def cancel_listener(self):
        show_toast("Login cancelled")
    
    def error_listener(self):
        show_toast("Error logging in.")
    
    def tiles_touched(self, inst):
        Logger.info("Hahaha: Tile Number={}".format(inst.tile_no))
        if self.previous_tile_inst:
            self.hide_box_anim(self.previous_tile_inst)

        if inst.box_y==.5:
            self.hide_box_anim(inst)
        else:
            self.show_box_anim(inst)

        self.previous_tile_inst= inst
    
    def show_box_anim(self, widget):
        anim= Animation(
            d=.1,
            box_color_alpha=.4,
            t= "out_back"
        )
        anim+= Animation(
            d=.15,
            box_y=.5,
            box_opacity=1,
            t="out_back"
        )
        anim.stop_all(widget)
        anim.start(widget)
    
    def hide_box_anim(self, widget):
        anim= Animation(
            d=.15,
            box_y=-.3,
            box_opacity=0,
            t="in_cubic"
        )
        anim+= Animation(
            d=.1,
            box_color_alpha=0,
            t= "in_cubic"
        )
        anim.stop_all(widget)
        anim.start(widget)
    
    def add_image(self):
        if PERMISSION_GRANTED==0:
            self.open_gallery()
            
        else:
            show_toast("Cannot work without providing this permission")
    
    def upload_images(self, file_path):
        '''
        if not self.selected_images_dummy==self.selected_images:
            data=[]
            for file_path in self.selected_images:
                skylink= skynet.upload_file(file_path)
                Logger.info("Hahaha: SkyLink={}".format(skylink))

                tmp={
                    'source': file_path,
                    'skylink': "https://siasky.net/"+skynet.strip_prefix(skylink),
                    'spinner_text': "",
                    'spinner_active':False,
                    'spinner_box_alpha':0,
                    'upload_done':True

                }

                data.append(tmp)
            
            new_data= self.root.ids.upload_screen.ids.rv.data+data
            self.root.ids.upload_screen.ids.rv.data= []
            self.root.ids.upload_screen.ids.rv.data.extend(new_data)
            Logger.info("Hahaha: RV_DATA_after= {}".format(self.root.ids.upload_screen.ids.rv.data))
            self.selected_images_dummy=self.selected_images'''


                #data= self.root.ids.upload_screen.ids.rv.data[idx]
        #data['source']= "https://siasky.net/"+skynet.strip_prefix(skylink)
        # data['skylink']= "https://siasky.net/"+skynet.strip_prefix(skylink)
        # data[]= 
        # data[]= 
        # data[]=0
        # data[]= True

        #_clean_cache()
        #self.root.ids.upload_screen.ids.rv.data.append(data)
        #self.root.ids.upload_screen.ids.rv.data.reverse()
        #self.root.ids.upload_screen.ids.rv.refresh_from_data()
        #self.root.ids.upload_screen.ids.rv.refresh_from_data()
        #self.root.ids.upload_screen.ids.rv.refresh_from_layout()
        #Logger.info("Hahaha: RV_DATA_after= {}".format(self.root.ids.upload_screen.ids.rv.data))

        grid= self.root.ids.upload_screen.ids.grid
        tile= SmartTiles()
        tile.source= file_path
        grid.add_widget(tile)

        
        skylink= skynet.upload_file(file_path)
        Logger.info("Hahaha: SkyLink={}".format(skylink))
        
        tile.skylink= "https://siasky.net/"+self.strip_prefix(skylink)
        tile.spinner_text= ""
        tile.spinner_active= False
        tile.spinner_box_alpha= 0
        tile.upload_done= True
    
    def strip_prefix(self, string):
        if string.startswith(skynet.uri_skynet_prefix()):
            return string[len(skynet.uri_skynet_prefix()):]
        return string
    
    def create_download_directory(self):
        if not os.path.exists(download_directory):
            os.makedirs(download_directory)
    
    def make_skylink(self, link):
        if link.startswith("https://siasky.net/"):
            return skynet.uri_skynet_prefix()+link[len("https://siasky.net/"):]
        return link
    
    def share_skylink(self, inst):
        skylink= inst.skylink
        if skylink:
            send_intent= Intent()
            send_intent.setAction(Intent.ACTION_SEND)
            send_intent.putExtra(Intent.EXTRA_TEXT, String(skylink))
            send_intent.setType(String("text/*"))

            share_intent = Intent.createChooser(send_intent, cast(CharSequence, String("Send SkyLink")))
            context.startActivity(share_intent)
            self.hide_box_anim(inst)
    
    def show_link_popup(self):
        if not self.dialog:
            self.dialog = MDDialog(
                title="Image Link",
                type="custom",
                content_cls=Content(),
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        text_color=self.theme_cls.primary_color,
                        on_release=self.cancel_dialog
                    ),
                    MDFlatButton(
                        text="OK",
                        text_color=self.theme_cls.primary_color,
                        on_release= self._download_image
                    ),
                ],
            )
        self.dialog.auto_dismiss= False
        self.dialog.open()
    
    def _download_image(self, *args):
        self.cancel_dialog()
        #self.download_image()
        # t = threading.Thread(
        #     target=self.download_image
        # )
        # t.start()
        Clock.schedule_once(self.download_image, .3)
    
    def download_image(self, *args):

        grid= self.root.ids.download_screen.ids.grid
        tile= SmartTiles()
        tile.source= "placeholder.jpg"
        tile.spinner_text= "Downloading..."
        grid.add_widget(tile)
        
        link= self.dialog.content_cls.children[0].text
        self.dialog.content_cls.children[0].text=""
        skylink= self.make_skylink(link)
        Logger.info("Hahaha: {}".format(skylink))

        file_path= download_directory+"/"+time.strftime("%d%m%Y_%H%M%S")+".jpg"
        
        try:
            # t= threading.Thread(
            #     target= lambda *args: func(file_path, skylink, tile, grid)
            # )
            # t.start()
            #t.join()
            skynet.download_file(file_path, skylink)
            
            tile.source=file_path
            tile.skylink= "https://siasky.net/"+self.strip_prefix(skylink)
            tile.spinner_text= ""
            tile.spinner_active= False
            tile.spinner_box_alpha= 0
            tile.upload_done= True
        except:
            grid.remove_widget(tile)
            show_toast("Error in downloading. Maybe an invalid link")
    
    def cancel_dialog(self, *args):
        self.dialog.dismiss()
    
    def func(self, file_path, skylink, tile, grid):
        # tile.source= "/storage/emulated/0/SkyShare/downloads/17082020_121003.jpg"
        # tile.spinner_text= "Downloading..."
        # grid.add_widget(tile)

        skynet.download_file(file_path, skylink)
        '''
        tile= SmartTiles()
        grid.remove_widget(tile)
        Logger.info("Hahaha: source={}".format(file_path))
        tile.source= ""
        Logger.info("Hahaha: source={}".format(tile.source))
        
        tile.skylink= "https://siasky.net/"+self.strip_prefix(skylink)
        tile.spinner_text= ""
        tile.spinner_active= False
        tile.spinner_box_alpha= 0
        tile.upload_done= True

        grid.add_widget(tile)'''


if __name__ == "__main__":
    SaveImageApp().run()