from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv
import mysql.connector
import os
import html
from datetime import date, datetime


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

app = Flask(__name__)

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://127.0.0.1:5500",
                "http://localhost:5500"
            ]
        }
    }
)


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "lifeadmin")
DB_PORT = int(os.getenv("DB_PORT", "3306"))


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():

    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )


def create_database():

    connection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

    cursor = connection.cursor()

    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`"
    )

    connection.commit()

    cursor.close()
    connection.close()


# ============================================================
# CREATE TABLES
# ============================================================

def create_tables():

    connection = get_db_connection()
    cursor = connection.cursor()

    # DOCUMENTS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(150) NOT NULL,
            category VARCHAR(50) NOT NULL,
            document_number VARCHAR(100),
            issue_date DATE,
            expiry_date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ON UPDATE CURRENT_TIMESTAMP
        )
    """)

    # BILLS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            due_date DATE NOT NULL,
            category VARCHAR(50),
            recurring BOOLEAN DEFAULT FALSE,
            frequency VARCHAR(20),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ON UPDATE CURRENT_TIMESTAMP
        )
    """)

    # SUBSCRIPTIONS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            billing_cycle VARCHAR(20) NOT NULL,
            next_billing_date DATE NOT NULL,
            category VARCHAR(50),
            status VARCHAR(20) DEFAULT 'Active',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ON UPDATE CURRENT_TIMESTAMP
        )
    """)

    # MOBILE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mobile_recharges (
            id INT AUTO_INCREMENT PRIMARY KEY,
            mobile_number VARCHAR(15) NOT NULL,
            operator VARCHAR(30) NOT NULL,
            plan VARCHAR(100) NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            recharge_date DATE NOT NULL,
            expiry_date DATE NOT NULL,
            frequency VARCHAR(30),
            auto_renew BOOLEAN DEFAULT FALSE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ON UPDATE CURRENT_TIMESTAMP
        )
    """)

    # WARRANTIES
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warranties (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product VARCHAR(150) NOT NULL,
            purchase_date DATE NOT NULL,
            expiry_date DATE NOT NULL,
            provider VARCHAR(150),
            serial_number VARCHAR(100),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ON UPDATE CURRENT_TIMESTAMP
        )
    """)

    # APPOINTMENTS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(150) NOT NULL,
            date DATE NOT NULL,
            time TIME,
            location VARCHAR(200),
            category VARCHAR(50),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ON UPDATE CURRENT_TIMESTAMP
        )
    """)

    connection.commit()

    cursor.close()
    connection.close()


# ============================================================
# HELPER
# ============================================================

def convert_dates(row):

    for key, value in row.items():

        if isinstance(value, (date, datetime)):
            row[key] = value.isoformat()

    return row


# ============================================================
# HEALTH
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():

    try:

        create_database()
        create_tables()

        return jsonify({
            "status": "success",
            "message": "LifeAdmin API is healthy",
            "database": DB_NAME
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================================
# TEST DATABASE
# ============================================================

@app.route("/api/test-db", methods=["GET"])
def test_db():

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT DATABASE()")

        result = cursor.fetchone()

        cursor.close()
        connection.close()

        return jsonify({
            "database": result[0],
            "status": "connected"
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================================
# DOCUMENTS
# ============================================================

@app.route("/api/documents", methods=["GET"])
def get_documents():

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                title,
                category,
                document_number,
                issue_date,
                expiry_date,
                notes
            FROM documents
            ORDER BY expiry_date ASC
        """)

        rows = cursor.fetchall()

        cursor.close()
        connection.close()

        return jsonify([
            convert_dates(row)
            for row in rows
        ])

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/documents", methods=["POST"])
def create_document():

    try:

        data = request.get_json()

        if not data.get("title"):
            return jsonify({"error": "Title is required"}), 400

        if not data.get("category"):
            return jsonify({"error": "Category is required"}), 400

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO documents
            (
                title,
                category,
                document_number,
                issue_date,
                expiry_date,
                notes
            )
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            data["title"],
            data["category"],
            data.get("document_number"),
            data.get("issue_date") or None,
            data.get("expiry_date") or None,
            data.get("notes")
        ))

        connection.commit()

        new_id = cursor.lastrowid

        cursor.close()
        connection.close()

        return jsonify({
            "message": "Document created successfully",
            "id": new_id
        }), 201

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/documents/<int:document_id>", methods=["GET"])
def get_document(document_id):

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                title,
                category,
                document_number,
                issue_date,
                expiry_date,
                notes
            FROM documents
            WHERE id = %s
        """, (document_id,))

        row = cursor.fetchone()

        cursor.close()
        connection.close()

        if not row:
            return jsonify({"error": "Document not found"}), 404

        return jsonify(convert_dates(row))

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/documents/<int:document_id>", methods=["PUT"])
def update_document(document_id):

    try:

        data = request.get_json()

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE documents
            SET
                title = %s,
                category = %s,
                document_number = %s,
                issue_date = %s,
                expiry_date = %s,
                notes = %s
            WHERE id = %s
        """, (
            data["title"],
            data["category"],
            data.get("document_number"),
            data.get("issue_date") or None,
            data.get("expiry_date") or None,
            data.get("notes"),
            document_id
        ))

        connection.commit()

        changed = cursor.rowcount

        cursor.close()
        connection.close()

        if changed == 0:
            return jsonify({"error": "Document not found"}), 404

        return jsonify({
            "message": "Document updated successfully"
        })

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/documents/<int:document_id>", methods=["DELETE"])
def delete_document(document_id):

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM documents
            WHERE id = %s
        """, (document_id,))

        connection.commit()

        changed = cursor.rowcount

        cursor.close()
        connection.close()

        if changed == 0:
            return jsonify({"error": "Document not found"}), 404

        return jsonify({
            "message": "Document deleted successfully"
        })

    except Exception as e:

        return jsonify({"error": str(e)}), 500


# ============================================================
# BILLS & PAYMENTS
# ============================================================

@app.route("/api/bills", methods=["GET"])
def get_bills():

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                name,
                amount,
                due_date,
                category,
                recurring,
                frequency,
                notes
            FROM bills
            ORDER BY due_date ASC
        """)

        rows = cursor.fetchall()

        cursor.close()
        connection.close()

        for row in rows:

            row = convert_dates(row)
            row["recurring"] = bool(row["recurring"])

        return jsonify(rows)

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/bills", methods=["POST"])
def create_bill():

    try:

        data = request.get_json()

        if not data.get("name"):
            return jsonify({"error": "Bill name is required"}), 400

        if data.get("amount") is None:
            return jsonify({"error": "Amount is required"}), 400

        if not data.get("due_date"):
            return jsonify({"error": "Due date is required"}), 400

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO bills
            (
                name,
                amount,
                due_date,
                category,
                recurring,
                frequency,
                notes
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            data["name"],
            data["amount"],
            data["due_date"],
            data.get("category"),
            bool(data.get("recurring", False)),
            data.get("frequency"),
            data.get("notes")
        ))

        connection.commit()

        new_id = cursor.lastrowid

        cursor.close()
        connection.close()

        return jsonify({
            "message": "Bill created successfully",
            "id": new_id
        }), 201

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/bills/<int:bill_id>", methods=["GET"])
def get_bill(bill_id):

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                name,
                amount,
                due_date,
                category,
                recurring,
                frequency,
                notes
            FROM bills
            WHERE id = %s
        """, (bill_id,))

        row = cursor.fetchone()

        cursor.close()
        connection.close()

        if not row:
            return jsonify({"error": "Bill not found"}), 404

        row = convert_dates(row)
        row["recurring"] = bool(row["recurring"])

        return jsonify(row)

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/bills/<int:bill_id>", methods=["PUT"])
def update_bill(bill_id):

    try:

        data = request.get_json()

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE bills
            SET
                name = %s,
                amount = %s,
                due_date = %s,
                category = %s,
                recurring = %s,
                frequency = %s,
                notes = %s
            WHERE id = %s
        """, (
            data["name"],
            data["amount"],
            data["due_date"],
            data.get("category"),
            bool(data.get("recurring", False)),
            data.get("frequency"),
            data.get("notes"),
            bill_id
        ))

        connection.commit()

        changed = cursor.rowcount

        cursor.close()
        connection.close()

        if changed == 0:
            return jsonify({"error": "Bill not found"}), 404

        return jsonify({
            "message": "Bill updated successfully"
        })

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/bills/<int:bill_id>", methods=["DELETE"])
def delete_bill(bill_id):

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM bills
            WHERE id = %s
        """, (bill_id,))

        connection.commit()

        changed = cursor.rowcount

        cursor.close()
        connection.close()

        if changed == 0:
            return jsonify({"error": "Bill not found"}), 404

        return jsonify({
            "message": "Bill deleted successfully"
        })

    except Exception as e:

        return jsonify({"error": str(e)}), 500


# ============================================================
# SUBSCRIPTIONS
# ============================================================

@app.route("/api/subscriptions", methods=["GET"])
def get_subscriptions():

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                name,
                amount,
                billing_cycle,
                next_billing_date,
                category,
                status,
                notes
            FROM subscriptions
            ORDER BY next_billing_date ASC
        """)

        rows = cursor.fetchall()

        cursor.close()
        connection.close()

        return jsonify([
            convert_dates(row)
            for row in rows
        ])

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/subscriptions", methods=["POST"])
def create_subscription():

    try:

        data = request.get_json()

        if not data.get("name"):
            return jsonify({"error": "Subscription name is required"}), 400

        if data.get("amount") is None:
            return jsonify({"error": "Amount is required"}), 400

        if not data.get("billing_cycle"):
            return jsonify({"error": "Billing cycle is required"}), 400

        if not data.get("next_billing_date"):
            return jsonify({"error": "Next billing date is required"}), 400

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO subscriptions
            (
                name,
                amount,
                billing_cycle,
                next_billing_date,
                category,
                status,
                notes
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            data["name"],
            data["amount"],
            data["billing_cycle"],
            data["next_billing_date"],
            data.get("category"),
            data.get("status", "Active"),
            data.get("notes")
        ))

        connection.commit()

        new_id = cursor.lastrowid

        cursor.close()
        connection.close()

        return jsonify({
            "message": "Subscription created successfully",
            "id": new_id
        }), 201

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/subscriptions/<int:subscription_id>", methods=["GET"])
def get_subscription(subscription_id):

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                name,
                amount,
                billing_cycle,
                next_billing_date,
                category,
                status,
                notes
            FROM subscriptions
            WHERE id = %s
        """, (subscription_id,))

        row = cursor.fetchone()

        cursor.close()
        connection.close()

        if not row:
            return jsonify({
                "error": "Subscription not found"
            }), 404

        return jsonify(convert_dates(row))

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/subscriptions/<int:subscription_id>", methods=["PUT"])
def update_subscription(subscription_id):

    try:

        data = request.get_json()

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE subscriptions
            SET
                name = %s,
                amount = %s,
                billing_cycle = %s,
                next_billing_date = %s,
                category = %s,
                status = %s,
                notes = %s
            WHERE id = %s
        """, (
            data["name"],
            data["amount"],
            data["billing_cycle"],
            data["next_billing_date"],
            data.get("category"),
            data.get("status", "Active"),
            data.get("notes"),
            subscription_id
        ))

        connection.commit()

        changed = cursor.rowcount

        cursor.close()
        connection.close()

        if changed == 0:
            return jsonify({
                "error": "Subscription not found"
            }), 404

        return jsonify({
            "message": "Subscription updated successfully"
        })

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/subscriptions/<int:subscription_id>", methods=["DELETE"])
def delete_subscription(subscription_id):

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM subscriptions
            WHERE id = %s
        """, (subscription_id,))

        connection.commit()

        changed = cursor.rowcount

        cursor.close()
        connection.close()

        if changed == 0:
            return jsonify({
                "error": "Subscription not found"
            }), 404

        return jsonify({
            "message": "Subscription deleted successfully"
        })

    except Exception as e:

        return jsonify({"error": str(e)}), 500


# ============================================================
# MOBILE & RECHARGE
# ============================================================

@app.route("/api/mobile-recharges", methods=["GET"])
def get_mobile_recharges():

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                mobile_number,
                operator,
                plan,
                amount,
                recharge_date,
                expiry_date,
                frequency,
                auto_renew,
                notes
            FROM mobile_recharges
            ORDER BY expiry_date ASC
        """)

        rows = cursor.fetchall()

        cursor.close()
        connection.close()

        for row in rows:

            row["recharge_date"] = (
                row["recharge_date"].isoformat()
                if row["recharge_date"] else None
            )

            row["expiry_date"] = (
                row["expiry_date"].isoformat()
                if row["expiry_date"] else None
            )

            row["auto_renew"] = bool(row["auto_renew"])

        return jsonify(rows)

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/mobile-recharges", methods=["POST"])
def create_mobile_recharge():

    try:

        data = request.get_json()

        required = [
            "mobile_number",
            "operator",
            "plan",
            "amount",
            "recharge_date",
            "expiry_date"
        ]

        for field in required:

            if not data.get(field):
                return jsonify({
                    "error": f"{field} is required"
                }), 400

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO mobile_recharges
            (
                mobile_number,
                operator,
                plan,
                amount,
                recharge_date,
                expiry_date,
                frequency,
                auto_renew,
                notes
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            data["mobile_number"],
            data["operator"],
            data["plan"],
            data["amount"],
            data["recharge_date"],
            data["expiry_date"],
            data.get("frequency"),
            bool(data.get("auto_renew", False)),
            data.get("notes")
        ))

        connection.commit()

        new_id = cursor.lastrowid

        cursor.close()
        connection.close()

        return jsonify({
            "message": "Mobile recharge created successfully",
            "id": new_id
        }), 201

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/mobile-recharges/<int:mobile_id>", methods=["GET"])
def get_mobile_recharge(mobile_id):

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                mobile_number,
                operator,
                plan,
                amount,
                recharge_date,
                expiry_date,
                frequency,
                auto_renew,
                notes
            FROM mobile_recharges
            WHERE id = %s
        """, (mobile_id,))

        row = cursor.fetchone()

        cursor.close()
        connection.close()

        if not row:
            return jsonify({
                "error": "Mobile recharge not found"
            }), 404

        row["recharge_date"] = (
            row["recharge_date"].isoformat()
            if row["recharge_date"] else None
        )

        row["expiry_date"] = (
            row["expiry_date"].isoformat()
            if row["expiry_date"] else None
        )

        row["auto_renew"] = bool(row["auto_renew"])

        return jsonify(row)

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/mobile-recharges/<int:mobile_id>", methods=["PUT"])
def update_mobile_recharge(mobile_id):

    try:

        data = request.get_json()

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE mobile_recharges
            SET
                mobile_number = %s,
                operator = %s,
                plan = %s,
                amount = %s,
                recharge_date = %s,
                expiry_date = %s,
                frequency = %s,
                auto_renew = %s,
                notes = %s
            WHERE id = %s
        """, (
            data["mobile_number"],
            data["operator"],
            data["plan"],
            data["amount"],
            data["recharge_date"],
            data["expiry_date"],
            data.get("frequency"),
            bool(data.get("auto_renew", False)),
            data.get("notes"),
            mobile_id
        ))

        connection.commit()

        changed = cursor.rowcount

        cursor.close()
        connection.close()

        if changed == 0:
            return jsonify({
                "error": "Mobile recharge not found"
            }), 404

        return jsonify({
            "message": "Mobile recharge updated successfully"
        })

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/mobile-recharges/<int:mobile_id>", methods=["DELETE"])
def delete_mobile_recharge(mobile_id):

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM mobile_recharges
            WHERE id = %s
        """, (mobile_id,))

        connection.commit()

        changed = cursor.rowcount

        cursor.close()
        connection.close()

        if changed == 0:
            return jsonify({
                "error": "Mobile recharge not found"
            }), 404

        return jsonify({
            "message": "Mobile recharge deleted successfully"
        })

    except Exception as e:

        return jsonify({"error": str(e)}), 500


# ============================================================
# WARRANTIES
# ============================================================

@app.route("/api/warranties", methods=["GET"])
def get_warranties():

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                product,
                purchase_date,
                expiry_date,
                provider,
                serial_number,
                notes
            FROM warranties
            ORDER BY expiry_date ASC
        """)

        rows = cursor.fetchall()

        cursor.close()
        connection.close()

        return jsonify([
            convert_dates(row)
            for row in rows
        ])

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/warranties", methods=["POST"])
def create_warranty():

    try:

        data = request.get_json()

        if not data.get("product"):
            return jsonify({"error": "Product is required"}), 400

        if not data.get("purchase_date"):
            return jsonify({"error": "Purchase date is required"}), 400

        if not data.get("expiry_date"):
            return jsonify({"error": "Expiry date is required"}), 400

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO warranties
            (
                product,
                purchase_date,
                expiry_date,
                provider,
                serial_number,
                notes
            )
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            data["product"],
            data["purchase_date"],
            data["expiry_date"],
            data.get("provider"),
            data.get("serial_number"),
            data.get("notes")
        ))

        connection.commit()

        new_id = cursor.lastrowid

        cursor.close()
        connection.close()

        return jsonify({
            "message": "Warranty created successfully",
            "id": new_id
        }), 201

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/warranties/<int:warranty_id>", methods=["GET"])
def get_warranty(warranty_id):

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                product,
                purchase_date,
                expiry_date,
                provider,
                serial_number,
                notes
            FROM warranties
            WHERE id = %s
        """, (warranty_id,))

        row = cursor.fetchone()

        cursor.close()
        connection.close()

        if not row:
            return jsonify({
                "error": "Warranty not found"
            }), 404

        return jsonify(convert_dates(row))

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/warranties/<int:warranty_id>", methods=["PUT"])
def update_warranty(warranty_id):

    try:

        data = request.get_json()

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE warranties
            SET
                product = %s,
                purchase_date = %s,
                expiry_date = %s,
                provider = %s,
                serial_number = %s,
                notes = %s
            WHERE id = %s
        """, (
            data["product"],
            data["purchase_date"],
            data["expiry_date"],
            data.get("provider"),
            data.get("serial_number"),
            data.get("notes"),
            warranty_id
        ))

        connection.commit()

        changed = cursor.rowcount

        cursor.close()
        connection.close()

        if changed == 0:
            return jsonify({
                "error": "Warranty not found"
            }), 404

        return jsonify({
            "message": "Warranty updated successfully"
        })

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/warranties/<int:warranty_id>", methods=["DELETE"])
def delete_warranty(warranty_id):

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM warranties
            WHERE id = %s
        """, (warranty_id,))

        connection.commit()

        changed = cursor.rowcount

        cursor.close()
        connection.close()

        if changed == 0:
            return jsonify({
                "error": "Warranty not found"
            }), 404

        return jsonify({
            "message": "Warranty deleted successfully"
        })

    except Exception as e:

        return jsonify({"error": str(e)}), 500


# ============================================================
# APPOINTMENTS
# ============================================================

@app.route("/api/appointments", methods=["GET"])
def get_appointments():

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                title,
                date,
                time,
                location,
                category,
                notes
            FROM appointments
            ORDER BY date ASC, time ASC
        """)

        rows = cursor.fetchall()

        cursor.close()
        connection.close()

        for row in rows:

            if row["date"]:
                row["date"] = row["date"].isoformat()

            if row["time"]:
                row["time"] = str(row["time"])

        return jsonify(rows)

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/api/appointments", methods=["POST"])
def create_appointment():

    try:

        data = request.get_json()

        if not data.get("title"):
            return jsonify({"error": "Title is required"}), 400

        if not data.get("date"):
            return jsonify({"error": "Date is required"}), 400

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO appointments
            (
                title,
                date,
                time,
                location,
                category,
                notes
            )
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            data["title"],
            data["date"],
            data.get("time"),
            data.get("location"),
            data.get("category"),
            data.get("notes")
        ))

        connection.commit()

        new_id = cursor.lastrowid

        cursor.close()
        connection.close()

        return jsonify({
            "message": "Appointment created successfully",
            "id": new_id
        }), 201

    except Exception as e:

        return jsonify({"error": str(e)}), 500


# ============================================================
# SEARCH
# ============================================================

@app.route("/api/search", methods=["GET"])
def search():

    query = request.args.get("q", "").strip().lower()

    if not query:
        return jsonify({"results": []})

    results = []

    tables = [
        ("documents", "Document"),
        ("bills", "Bill"),
        ("subscriptions", "Subscription"),
        ("mobile_recharges", "Mobile"),
        ("warranties", "Warranty"),
        ("appointments", "Appointment")
    ]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    for table, label in tables:

        if table == "documents":

            cursor.execute("""
                SELECT id, title AS name, category
                FROM documents
            """)

        elif table == "bills":

            cursor.execute("""
                SELECT id, name, category
                FROM bills
            """)

        elif table == "subscriptions":

            cursor.execute("""
                SELECT id, name, category
                FROM subscriptions
            """)

        elif table == "mobile_recharges":

            cursor.execute("""
                SELECT id, plan AS name, operator AS category
                FROM mobile_recharges
            """)

        elif table == "warranties":

            cursor.execute("""
                SELECT id, product AS name, provider AS category
                FROM warranties
            """)

        else:

            cursor.execute("""
                SELECT id, title AS name, category
                FROM appointments
            """)

        rows = cursor.fetchall()

        for row in rows:

            text = (
                str(row.get("name") or "")
                + " "
                + str(row.get("category") or "")
            ).lower()

            if query in text:

                results.append({
                    "id": row["id"],
                    "type": label,
                    "title": row.get("name")
                })

    cursor.close()
    connection.close()

    return jsonify({
        "results": results[:50]
    })


# ============================================================
# AI ASSISTANT BASIC API
# ============================================================

@app.route("/api/assistant", methods=["GET"])
def assistant():

    query = request.args.get("q", "").lower()

    if not query:

        return jsonify({
            "answer": (
                "<p>Ask me about your upcoming bills, "
                "subscriptions, documents or other obligations.</p>"
            )
        })

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT name, amount, due_date
        FROM bills
        ORDER BY due_date ASC
    """)

    bills = cursor.fetchall()

    cursor.close()
    connection.close()

    if "bill" in query:

        total = sum(
            float(row["amount"])
            for row in bills
        )

        return jsonify({
            "answer": (
                f"<p>You have <strong>{len(bills)}</strong> "
                f"bill record(s), totaling "
                f"<strong>₹{total:,.2f}</strong>.</p>"
            )
        })

    return jsonify({
        "answer": (
            "<p>I can help with <strong>bills, "
            "subscriptions, documents and upcoming "
            "obligations</strong>.</p>"
        )
    })


# ============================================================
# CALENDAR EXPORT
# ============================================================

@app.route("/api/calendar.ics", methods=["GET"])
def calendar():

    events = []

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Documents
    cursor.execute("""
        SELECT title, expiry_date
        FROM documents
        WHERE expiry_date IS NOT NULL
    """)

    for row in cursor.fetchall():

        events.append((
            row["expiry_date"],
            row["title"]
        ))

    # Bills
    cursor.execute("""
        SELECT name, due_date
        FROM bills
    """)

    for row in cursor.fetchall():

        events.append((
            row["due_date"],
            row["name"]
        ))

    # Subscriptions
    cursor.execute("""
        SELECT name, next_billing_date
        FROM subscriptions
    """)

    for row in cursor.fetchall():

        events.append((
            row["next_billing_date"],
            row["name"]
        ))

    # Mobile
    cursor.execute("""
        SELECT plan, expiry_date
        FROM mobile_recharges
    """)

    for row in cursor.fetchall():

        events.append((
            row["expiry_date"],
            row["plan"]
        ))

    # Warranties
    cursor.execute("""
        SELECT product, expiry_date
        FROM warranties
    """)

    for row in cursor.fetchall():

        events.append((
            row["expiry_date"],
            row["product"]
        ))

    # Appointments
    cursor.execute("""
        SELECT title, date
        FROM appointments
    """)

    for row in cursor.fetchall():

        events.append((
            row["date"],
            row["title"]
        ))

    cursor.close()
    connection.close()

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//LifeAdmin//EN"
    ]

    for event_date, title in events:

        if not event_date:
            continue

        stamp = event_date.strftime("%Y%m%d")

        safe_title = (
            str(title)
            .replace("\\", "\\\\")
            .replace(",", "\\,")
            .replace(";", "\\;")
        )

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:lifeadmin-{stamp}-{abs(hash(str(title)))}@lifeadmin",
            f"DTSTART;VALUE=DATE:{stamp}",
            f"SUMMARY:{safe_title}",
            "END:VEVENT"
        ])

    lines.append("END:VCALENDAR")

    return Response(
        "\r\n".join(lines) + "\r\n",
        mimetype="text/calendar",
        headers={
            "Content-Disposition":
            "attachment; filename=lifeadmin-calendar.ics"
        }
    )


# ============================================================
# SHOW ALL FLASK ROUTES
# ============================================================

@app.route("/api/routes", methods=["GET"])
def show_routes():

    routes = []

    for rule in app.url_map.iter_rules():

        routes.append({
            "path": str(rule),
            "methods": sorted(
                list(rule.methods - {"HEAD", "OPTIONS"})
            )
        })

    return jsonify(routes)


# ============================================================
# ROOT
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return "LifeAdmin Backend is running!"


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    create_database()
    create_tables()

    print("")
    print("============================================")
    print("       LIFEADMIN BACKEND")
    print("============================================")
    print("Database    :", DB_NAME)
    print("Server      : http://127.0.0.1:5000")
    print("")
    print("Documents   : /api/documents")
    print("Bills       : /api/bills")
    print("Subscriptions: /api/subscriptions")
    print("Mobile      : /api/mobile-recharges")
    print("Warranties  : /api/warranties")
    print("Appointments: /api/appointments")
    print("")
    print("Routes      : /api/routes")
    print("Health      : /api/health")
    print("============================================")
    print("")

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )