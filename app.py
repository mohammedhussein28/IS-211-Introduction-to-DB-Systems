from flask import Flask, render_template, request, redirect, url_for
from db import Database

app = Flask(__name__)
db = Database()


@app.route("/")
@app.route("/dashboard")
def dashboard():
    stats = {
        "total_units": db.fetch_one("SELECT COUNT(*) AS count FROM PowerUnit")["count"],
        "total_technicians": db.fetch_one("SELECT COUNT(*) AS count FROM Technician")["count"],
        "total_inspections": db.fetch_one("SELECT COUNT(*) AS count FROM Inspection")["count"],
        "critical_units": db.fetch_one("""
            SELECT COUNT(*) AS count
            FROM InspectionRecord
            WHERE status = 'Critical'
        """)["count"]
    }

    recent_inspections = db.fetch_all("""
        SELECT TOP 5
            i.inspection_id,
            i.inspection_date,
            pu.unit_type AS unit_name,
            t.fullname AS technician_name,
            ir.status
        FROM Inspection i
        JOIN InspectionRecord ir ON i.inspection_id = ir.inspection_id
        JOIN PowerUnit pu ON ir.unitID = pu.unitID
        JOIN Technician t ON i.techID = t.techID
        ORDER BY i.inspection_date DESC
    """)

    return render_template(
        "dashboard.html",
        stats=stats,
        recent_inspections=recent_inspections
    )


@app.route("/technicians")
def technicians():
    technicians = db.fetch_all("""
        SELECT
            techID AS technician_id,
            fullname AS technician_name,
            '' AS specialization,
            '' AS phone,
            '' AS email
        FROM Technician
        ORDER BY techID
    """)

    return render_template("technicians.html", technicians=technicians)


@app.route("/technicians/add", methods=["POST"])
def add_technician():
    tech_id = request.form.get("techID")
    name = request.form.get("technician_name")

    db.execute_query("""
        INSERT INTO Technician
        (techID, fullname)
        VALUES (?, ?)
    """, (tech_id, name))

    return redirect(url_for("technicians"))


@app.route("/technicians/edit/<int:id>", methods=["POST"])
def edit_technician(id):
    name = request.form.get("technician_name")

    db.execute_query("""
        UPDATE Technician
        SET fullname = ?
        WHERE techID = ?
    """, (name, id))

    return redirect(url_for("technicians"))


@app.route("/technicians/delete/<int:id>", methods=["POST"])
def delete_technician(id):
    # First delete from TechnicianCertification (child table)
    db.execute_query("DELETE FROM TechnicianCertification WHERE techID = ?", (id,))
    
    # Then delete from InspectionRecord through Inspection
    db.execute_query("""
        DELETE FROM InspectionRecord
        WHERE inspection_id IN (
            SELECT inspection_id FROM Inspection WHERE techID = ?
        )
    """, (id,))
    
    # Then delete from Inspection
    db.execute_query("DELETE FROM Inspection WHERE techID = ?", (id,))
    
    # Finally delete from Technician
    db.execute_query("DELETE FROM Technician WHERE techID = ?", (id,))
    
    return redirect(url_for("technicians"))

@app.route("/power-units")
def power_units():
    search = request.args.get("search", "")
    status_filter = request.args.get("status", "")

    query = """
        SELECT
            pu.unitID AS unit_id,
            pu.manufacturer AS unit_name,
            pu.manufacturer,
            pu.unit_type,
            pu.max_output AS capacity,
            pu.siteID AS location,
            pu.install_date AS installation_date,
            ISNULL((
                SELECT TOP 1 ir.status
                FROM InspectionRecord ir
                WHERE ir.unitID = pu.unitID
                ORDER BY ir.record_id DESC
            ), 'Operational') AS status
        FROM PowerUnit pu
        WHERE 1=1
    """

    params = []

    if search:
        query += " AND (pu.manufacturer LIKE ? OR pu.unit_type LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if status_filter:
        query += """
            AND ISNULL((
                SELECT TOP 1 ir.status
                FROM InspectionRecord ir
                WHERE ir.unitID = pu.unitID
                ORDER BY ir.record_id DESC
            ), 'Operational') = ?
        """
        params.append(status_filter)

    query += " ORDER BY pu.unitID"

    units = db.fetch_all(query, tuple(params))

    sites = db.fetch_all("""
        SELECT siteID
        FROM EnergySite
        ORDER BY siteID
    """)

    return render_template(
        "power_units.html",
        units=units,
        sites=sites,
        search=search,
        status_filter=status_filter
    )


@app.route("/power-units/add", methods=["POST"])
def add_power_unit():
    unit_id = db.next_id("PowerUnit", "unitID")

    manufacturer = request.form.get("unit_name")
    unit_type = request.form.get("unit_type")
    max_output = request.form.get("capacity")
    site_id = request.form.get("location")
    install_date = request.form.get("installation_date")

    db.execute_query("""
        INSERT INTO PowerUnit
        (unitID, manufacturer, install_date, max_output, siteID, unit_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (unit_id, manufacturer, install_date, max_output, site_id, unit_type))

    return redirect(url_for("power_units"))


@app.route("/power-units/edit/<int:id>", methods=["POST"])
def edit_power_unit(id):
    manufacturer = request.form.get("unit_name")
    unit_type = request.form.get("unit_type")
    max_output = request.form.get("capacity")
    site_id = request.form.get("location")
    install_date = request.form.get("installation_date")

    db.execute_query("""
        UPDATE PowerUnit
        SET manufacturer = ?, install_date = ?, max_output = ?, siteID = ?, unit_type = ?
        WHERE unitID = ?
    """, (manufacturer, install_date, max_output, site_id, unit_type, id))

    return redirect(url_for("power_units"))


@app.route("/power-units/delete/<int:id>", methods=["POST"])
def delete_power_unit(id):
    db.execute_query("DELETE FROM InspectionRecord WHERE unitID = ?", (id,))
    db.execute_query("DELETE FROM ReplacementPart WHERE replacement_id IN (SELECT replacement_id FROM Replacement WHERE unitID = ?)", (id,))
    db.execute_query("DELETE FROM Replacement WHERE unitID = ?", (id,))
    db.execute_query("DELETE FROM PowerUnit WHERE unitID = ?", (id,))

    return redirect(url_for("power_units"))


@app.route("/inspections")
def inspections():
    inspections = db.fetch_all("""
        SELECT
            i.inspection_id,
            i.inspection_date,
            pu.unit_type AS unit_name,
            pu.unitID AS unit_id,
            t.fullname AS technician_name,
            t.techID AS technician_id,
            ir.status
        FROM Inspection i
        JOIN InspectionRecord ir ON i.inspection_id = ir.inspection_id
        JOIN PowerUnit pu ON ir.unitID = pu.unitID
        JOIN Technician t ON i.techID = t.techID
        ORDER BY i.inspection_date DESC
    """)

    units = db.fetch_all("""
        SELECT unitID AS unit_id, unit_type AS unit_name
        FROM PowerUnit
        ORDER BY unitID
    """)

    technicians = db.fetch_all("""
        SELECT techID AS technician_id, fullname AS technician_name
        FROM Technician
        ORDER BY fullname
    """)

    return render_template(
        "inspections.html",
        inspections=inspections,
        units=units,
        technicians=technicians
    )


@app.route("/inspections/add", methods=["POST"])
def add_inspection():
    inspection_id = db.next_id("Inspection", "inspection_id")
    record_id = db.next_id("InspectionRecord", "record_id")

    unit_id = request.form.get("unit_id")
    technician_id = request.form.get("technician_id")
    inspection_date = request.form.get("inspection_date")
    status = request.form.get("status")

    site_row = db.fetch_one("SELECT siteID FROM PowerUnit WHERE unitID = ?", (unit_id,))
    site_id = site_row["siteID"]

    db.execute_query("""
        INSERT INTO Inspection
        (inspection_id, siteID, techID, inspection_date)
        VALUES (?, ?, ?, ?)
    """, (inspection_id, site_id, technician_id, inspection_date))

    db.execute_query("""
        INSERT INTO InspectionRecord
        (record_id, unitID, inspection_id, efficiency_reading, status)
        VALUES (?, ?, ?, ?, ?)
    """, (record_id, unit_id, inspection_id, 80.00, status))

    return redirect(url_for("inspections"))


@app.route("/inspections/delete/<int:id>", methods=["POST"])
def delete_inspection(id):
    db.execute_query("DELETE FROM InspectionRecord WHERE inspection_id = ?", (id,))
    db.execute_query("DELETE FROM Inspection WHERE inspection_id = ?", (id,))

    return redirect(url_for("inspections"))


@app.route("/replacements")
def replacements():
    replacements = db.fetch_all("""
        SELECT
            r.replacement_id,
            r.replacement_date,
            pu.unit_type AS unit_name,
            pu.unitID AS unit_id,
            ISNULL(sp.part_name, rp.serial_no) AS component_name,
            ISNULL(rp.quantity_used, 0) AS quantity
        FROM Replacement r
        JOIN PowerUnit pu ON r.unitID = pu.unitID
        LEFT JOIN ReplacementPart rp ON r.replacement_id = rp.replacement_id
        LEFT JOIN SparePart sp ON rp.serial_no = sp.serial_no
        ORDER BY r.replacement_date DESC
    """)

    units = db.fetch_all("""
        SELECT unitID AS unit_id, unit_type AS unit_name
        FROM PowerUnit
        ORDER BY unitID
    """)

    # Fetch all spare parts for the dropdown
    spare_parts = db.fetch_all("""
        SELECT serial_no, part_name
        FROM SparePart
        ORDER BY serial_no
    """)

    return render_template(
        "replacements.html",
        replacements=replacements,
        units=units,
        spare_parts=spare_parts
    )

@app.route("/replacements/add", methods=["POST"])
def add_replacement():
    replacement_id = db.next_id("Replacement", "replacement_id")

    unit_id = request.form.get("unit_id")
    replacement_date = request.form.get("replacement_date")
    serial_no = request.form.get("serial_no")
    quantity = request.form.get("quantity")

    db.execute_query("""
        INSERT INTO Replacement
        (replacement_id, replacement_date, unitID)
        VALUES (?, ?, ?)
    """, (replacement_id, replacement_date, unit_id))

    db.execute_query("""
        INSERT INTO ReplacementPart
        (replacement_id, serial_no, quantity_used)
        VALUES (?, ?, ?)
    """, (replacement_id, serial_no, quantity))

    return redirect(url_for("replacements"))


@app.route("/replacements/delete/<int:id>", methods=["POST"])
def delete_replacement(id):
    db.execute_query("DELETE FROM ReplacementPart WHERE replacement_id = ?", (id,))
    db.execute_query("DELETE FROM Replacement WHERE replacement_id = ?", (id,))

    return redirect(url_for("replacements"))


@app.route("/reports")
def reports():
    units_by_status = db.fetch_all("""
        SELECT status, COUNT(*) AS count
        FROM InspectionRecord
        GROUP BY status
    """)

    inspections_by_status = db.fetch_all("""
        SELECT status, COUNT(*) AS count
        FROM InspectionRecord
        GROUP BY status
    """)

    units_by_type = db.fetch_all("""
        SELECT unit_type, COUNT(*) AS count
        FROM PowerUnit
        GROUP BY unit_type
    """)

    total_capacity = db.fetch_one("""
        SELECT ISNULL(SUM(max_output), 0) AS total
        FROM PowerUnit
    """)

    return render_template(
        "reports.html",
        units_by_status=units_by_status,
        inspections_by_status=inspections_by_status,
        units_by_type=units_by_type,
        total_capacity=total_capacity["total"]
    )


if __name__ == "__main__":
    app.run(debug=True)