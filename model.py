# models.py

class Product:
    def __init__(self, productID, name, description, cost, price, category):
        self.productID = productID
        self.name = name
        self.description = description
        self.cost = cost
        self.price = price
        self.category = category

    def getDetails(self):
        return f"{self.name} - {self.category} - {self.price}฿"

class Inventory:
    def __init__(self, inventoryID, product, quantity):
        self.inventoryID = inventoryID
        self.product = product
        self.quantity = quantity

    def adjustQuantity(self, delta):
        self.quantity += delta

    def getproductInfo(self):
        return f"{self.product.getDetails()} | คงเหลือ: {self.quantity}"


class Warehouse:
    def __init__(self, warehouseID, name, location):
        self.warehouseID = warehouseID
        self.name = name
        self.location = location
        self.inventoryList = []

    def addProduct(self, product, quantity):
        # เพิ่มสินค้าหรือเพิ่มจำนวนถ้ามีอยู่แล้ว
        for item in self.inventoryList:
            if item.product.productID == product.productID:
                item.adjustQuantity(quantity)
                return
        newInventory = Inventory(len(self.inventoryList)+1, product, quantity)
        self.inventoryList.append(newInventory)

    def removeProduct(self, product, quantity):
        # ลดจำนวนสินค้าหรือเอาออกถ้าหมด
        for item in self.inventoryList:
            if item.product.productID == product.productID:
                item.adjustQuantity(-quantity)
                if item.quantity <= 0:
                    self.inventoryList.remove(item)
                return

    def getProductByID(self, productID):
        for item in self.inventoryList:
            if item.product.productID == productID:
                return item.product
        return None

# ✅ User class
class User:
    def __init__(self, userID, username, password, role):
        self.userID = userID
        self.username = username
        self.password = password
        self.role = role

    def addUser(self, username, password):
        # ในระบบจริงจะมีการบันทึกลง DB
        print(f"เพิ่มผู้ใช้: {username}")

