import PicoLCD18 as lcd
from machine import Pin
import micropython
import time

# micropython reference says this is good practice for interrupts, so I'm doing it I guess
micropython.alloc_emergency_exception_buf(100)


button_up = Pin(2, Pin.IN, Pin.PULL_UP)
button_down = Pin(3, Pin.IN, Pin.PULL_UP)
button_press = Pin(4, Pin.IN, Pin.PULL_UP)




class Menu():
    def __init__(self, is_parent, is_child, title, parent=None) -> None:
        # To be used for submenus
        self.is_parent = bool(is_parent)
        self.is_child = bool(is_child)
        self.parent = parent
        self.in_focus = False
        self.root_menu = self.get_root()
        
        # Formatting constants
        self.ITEM_SPACING = 15
        self.MARGIN = 10
        self.ITEM_MARGIN = 5
    
        self.title = str(title)
        self.title_x = self.MARGIN
        self.title_y = 10

        # Keep track of menu items and navigation
        self.items = []
        self.selected_item = 0
        self.direction = 0
        self.item_selected = False
        

        # Predefine color values
        self.WHITE = 0xFFFF
        self.BLACK = 0x0000
        self.GREEN = 0x001F
        self.BLUE = 0xF800
        self.RED = 0x07E0
        self.BG_COLOR = self.BLACK
        self.TEXT_COLOR = self.GREEN
        self.HIGHLIGHT_COLOR = self.WHITE

        # Set up lcd stuffs 
        self.lcd = lcd.LCD_1inch8()
        self.lcd.rect(0, 0, 160, 128, self.BLACK, True)
        

        # Initialize top parent menu in focus
        if self.is_parent and not self.is_child:
            self.set_focus(True)
            self.active_menu = self

        # Add menuitem to navigate back to previous menu
        elif self.is_child:
            if self.parent:
                back = MenuItem(self.parent.title, self.close, "option")
                self.add(back)


    def get_root(self):
        if self.parent:
            return self.parent.get_root()
        return self

            

    def activate_buttons(self):
        button_up.irq(trigger=Pin.IRQ_FALLING, handler=self.handle_button_press)
        button_down.irq(trigger=Pin.IRQ_FALLING, handler=self.handle_button_press)
        button_press.irq(trigger=Pin.IRQ_FALLING, handler=self.handle_button_press)

    
    def deactivate_buttons(self):
        button_up.irq(handler=None)
        button_down.irq(handler=None)
        button_press.irq(handler=None)


    
    def set_focus(self, value):
        #global current_menu
        self.in_focus = bool(value)
        if value:
            #current_menu = self
            root_menu = self.get_root()
            root_menu.active_menu = self
            self.activate_buttons()
        else:
            self.deactivate_buttons()
        
    
    def flip_focus(self):
        self.in_focus = not self.in_focus
        self.switch_buttons()
    
    
    def switch_buttons(self):
        if self.in_focus:
            self.activate_buttons()
        else:
            self.deactivate_buttons()
            
    
    def create_title(self):
        self.lcd.rect(self.title_x,  self.title_y, self.lcd.width, 8, self.BG_COLOR, True)
        self.lcd.rect(self.title_x-4, self.title_y-4, self.lcd.width-12, 16, self.GREEN)
        self.lcd.text(self.title, self.title_x, self.title_y, self.GREEN)
        if self.is_child:
            self.lcd.text("^", self.lcd.width-20, self.title_y, self.GREEN)
        self.lcd.show()
    

    def close(self):
        #global current_menu
        if self.parent:
            self.set_focus(False)
            self.parent.set_focus(True)
            root_menu = self.get_root()
            root_menu.active_menu = self.parent
            #current_menu = self.parent

    
    def add(self, item):
        self.items.append(item)


    def remove(self, item):
        self.items.remove(item)


    def getItems(self):
        return self.items
    
    
    # Run menuitem
    def run_item(self):
        if self.items[self.selected_item].type == "option":
            self.items[self.selected_item].run()

        # if item is submenu, submenu gains focus, and supermenu loses focus
        elif self.items[self.selected_item].type == "submenu":
            self.flip_focus()
            self.items[self.selected_item].target.flip_focus()
            self.items[self.selected_item].run()


    def navigate(self):
        # divide by 0 proofing
        if len(self.items) == 0:
            return
        if self.item_selected:
            self.run_item()
            self.item_selected = False
        # use % to wrap around menu items
        self.selected_item = (self.selected_item + self.direction) % len(self.items)
        self.direction = 0
        
    

    def set_position(self, item, index):
        # set menu item position
        item.set_x(self.MARGIN + self.ITEM_MARGIN)
        item.set_y(self.title_y + self.ITEM_SPACING * (index + 1))


    def render(self):
        # Iterate over items in item list and write them to their assigned x & y coordinates
        for index, item in enumerate(self.items):
            self.set_position(item, index)
            
            # if item has same index position in self.items as selected item, highlight it
            if index == self.selected_item:
                color = self.HIGHLIGHT_COLOR
                string = ">" + item.label
                self.lcd.rect(item.x, item.y, self.lcd.width, 10, self.BLACK, True)
                self.lcd.rect(item.x, item.y+8, len(string)*8, 1, self.WHITE)
            
            # if item is not selected item, render as normal
            else:
                color = self.TEXT_COLOR
                string = item.label
                self.lcd.rect(item.x, item.y, self.lcd.width, 10, self.BLACK, True)
            self.lcd.text(string, item.x, item.y, color)
        self.lcd.show()


    def handle_button_press(self, pin):
        if self.in_focus:

            # navigate up and down
            if pin == button_up and not button_up.value():
                self.direction = -1
            elif pin == button_down and not button_down.value():
                self.direction = 1

            # run option
            elif pin == button_press and not button_press.value():
                self.item_selected = True
            time.sleep(0.05)
    

    def update(self):
        if self.root_menu.active_menu.in_focus:
            self.root_menu.active_menu.create_title()
            self.root_menu.active_menu.navigate()
            self.root_menu.active_menu.render()




class MenuItem:
    def __init__(self, label, target, type):
        self.label = str(label)
        self.target = target
        self.x = 10
        self.y = 10
        self.type = str(type)

    def set_x(self, x):
        self.x = x
    
    def get_x(self):
        return self.x
    
    def set_y(self, y):
        self.y = y
    
    def get_y(self):
        return self.y
    
    def run(self):
        global current_menu
        if isinstance(self.target, Menu):
            #current_menu = self.target
            root_menu = self.target.get_root()
            root_menu.active_menu = self.target
        else:
            self.target()



def f1():
    print("func1")

def f2():
    print("func2")

def f3():
    print("func3")



menu = Menu(is_parent=True, is_child=False, title="MAIN MENU")



item_1 = MenuItem("Option 1", f1, "option")
item_2 = MenuItem("Option 2", f2, "option")
item_3 = MenuItem(label="Option 3", target=f3, type="option")

sub_option = MenuItem("Sub Option 1", f1, "option")
sub_menu = Menu(is_parent=True, is_child=True, title="SUB MENU", parent=menu)
sub_menu.add(sub_option)
sub_menu_item = MenuItem(label=sub_menu.title, target=sub_menu, type="submenu")


sub_sub = Menu(True, True, "SUB SUB MENU", sub_menu)
sub_sub_item = MenuItem(sub_sub.title, sub_sub, "submenu")
sub_menu.add(sub_sub_item)

menu.add(sub_menu_item)
menu.add(item_2)
menu.add(item_3)
menu.add(item_3)
menu.add(item_3)
menu.add(item_3)
menu.add(item_3)

# keeps track of which menu the user is currently navigating
#current_menu = menu

while True:
    menu.update()
