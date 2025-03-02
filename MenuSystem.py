import PicoLCD18 as lcd
from machine import Pin
import micropython
import time

# micropython reference says this is good practice, so I'm doing it I guess
micropython.alloc_emergency_exception_buf(100)


button_up = Pin(2, Pin.IN, Pin.PULL_UP)
button_down = Pin(3, Pin.IN, Pin.PULL_UP)
button_press = Pin(4, Pin.IN, Pin.PULL_UP)


class Menu():
    def __init__(self, is_parent, title) -> None:
        self.is_parent = bool(is_parent)
        
        self.ITEM_SPACING = 15
        self.MARGIN = 10
        self.ITEM_MARGIN = 5

        self.title = str(title)
        self.title_x = self.MARGIN
        self.title_y = 10

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

        self.lcd = lcd.LCD_1inch8()
        self.lcd.rect(0, 0, 160, 128, self.BLACK, True)
        


        button_up.irq(trigger=Pin.IRQ_FALLING, handler=self.handle_button_press)
        button_down.irq(trigger=Pin.IRQ_FALLING, handler=self.handle_button_press)
        button_press.irq(trigger=Pin.IRQ_FALLING, handler=self.handle_button_press)
        self.button_pressed = False

        if self.is_parent:
            self.lcd.rect(self.title_x-4, self.title_y-4, self.lcd.width, 16, self.GREEN)
            self.lcd.text(self.title, self.title_x, self.title_y, self.GREEN)
            self.lcd.show()

        elif not self.is_parent:
            back = MenuItem("<- Back", self.close())
            self.add(back)
        
        

    def close(self):
        #exit into other parent menu
        print("close")
        
    
    def add(self, item):
        self.items.append(item)


    def remove(self, item):
        self.items.remove(item)


    def getItems(self):
        return self.items
    
    
    def run_item(self):
        self.items[self.selected_item].run()


    def navigate(self):
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

            if index == self.selected_item:
                color = self.HIGHLIGHT_COLOR
                string = ">" + item.label
                self.lcd.rect(item.x, item.y, self.lcd.width, 10, self.BLACK, True)
                self.lcd.rect(item.x, item.y+8, len(string)*8, 1, self.WHITE)
            
            else:
                color = self.TEXT_COLOR
                string = item.label
                self.lcd.rect(item.x, item.y, self.lcd.width, 10, self.BLACK, True)
            self.lcd.text(string, item.x, item.y, color)
        self.lcd.show()


    def handle_button_press(self, pin):
        self.button_pressed = True

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
        self.navigate()
        self.render()



class MenuItem:
    def __init__(self, label, function):
        self.label = str(label)
        self.function = function
        self.x = 10
        self.y = 10

    def set_x(self, x):
        self.x = x
    
    def get_x(self):
        return self.x
    
    def set_y(self, y):
        self.y = y
    
    def get_y(self):
        return self.y
    
    def run(self):
        self.function()



menu = Menu(is_parent=True, title="MENU")





def f1():
    print("func1")

def f2():
    print("func2")

def f3():
    print("func3")


item_1 = MenuItem("Option 1", f1)
item_2 = MenuItem("Option 2", f2)
item_3 = MenuItem("Option 3", f3)

sub_menu = Menu(is_parent=False, title="SUB MENU")
item_sub = MenuItem(sub_menu.title, sub_menu.update)



menu.add(item_sub)
menu.add(item_2)
menu.add(item_3)
menu.add(item_3)
menu.add(item_3)
menu.add(item_3)
menu.add(item_3)




for item in menu.items:
    print(item.label)
    item.run()

"""while True:
    if not button_up.value():
        menu.navigate(1)
    elif not button_down.value():
        menu.navigate(-1)
    time.sleep(0.1)
"""


while True:
    menu.update()
