"""Small product-catalogue API used as the subject of the CI pipeline."""
import os

from flask import Flask, jsonify, request

app = Flask(__name__)

PRODUCTS = {
    1: {"name": "Notebook", "price": 50.0},
    2: {"name": "Pen", "price": 10.0},
    3: {"name": "Backpack", "price": 899.0},
}


def apply_discount(price, percent):
    """Return price after a percentage discount, rounded to 2 decimals."""
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return round(price * (100 + percent) / 100, 2)


def get_port():
    return int(os.environ.get("PORT", "5000"))


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/products/<int:pid>")
def get_product(pid):
    product = PRODUCTS.get(pid)
    if product is None:
        return jsonify(error="product not found"), 404
    return jsonify(id=pid, name=product["name"], price=product["price"])


@app.get("/products/<int:pid>/price")
def get_price(pid):
    product = PRODUCTS.get(pid)
    if product is None:
        return jsonify(error="product not found"), 404
    percent = float(request.args.get("discount", 0))
    return jsonify(id=pid, final_price=apply_discount(product["price"], percent))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=get_port())
