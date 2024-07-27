from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'inirahasiahehe'

def dbconnect():
    conn = sqlite3.connect('dbnilai.db')
    conn.row_factory = sqlite3.Row
    return conn

with app.app_context():
    conn = dbconnect()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mhs(
                NIM TEXT PRIMARY KEY,
                NAMA TEXT NOT NULL,
                JURUSAN TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lnilai(
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                NIM TEXT,
                TUGAS INTEGER,
                UTS INTEGER,
                UAS INTEGER,
                TOTAL INTEGER,
                RATA REAL,
                STATUS TEXT,
                GRADE TEXT,
                FOREIGN KEY (NIM) REFERENCES mhs (NIM))''')
    conn.commit()
    conn.close()

def hitnilstat(rata):
    if rata >= 85:
        return 'Lulus', 'A'
    elif rata >= 70:
        return 'Lulus', 'B'
    elif rata >= 55:
        return 'Tidak Lulus', 'C'
    elif rata >= 40:
        return 'Tidak Lulus', 'D'
    else:
        return 'Gagal', 'E'


@app.route('/')
def index():
    conn = dbconnect()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT mhs.NIM, mhs.NAMA, mhs.JURUSAN, lnilai.RATA, lnilai.STATUS
        FROM mhs
        LEFT JOIN lnilai ON mhs.NIM = lnilai.NIM
    ''')

    students = cursor.fetchall()
    conn.close()

    students_list = []
    for student in students:
        students_list.append({
            'nim': student['NIM'],
            'nama': student['NAMA'],
            'jurusan': student['JURUSAN'],
            'rata': student['RATA'],
            'status': student['STATUS']
        })

    return render_template('index.html', students=students_list)


@app.route('/add', methods=('GET', 'POST'))
def add():
    if request.method == 'POST':
        nim = request.form['nim']
        nama = request.form['nama']
        jurusan = request.form['jurusan']
        tugas = request.form['tugas']
        uts = request.form['uts']
        uas = request.form['uas']

        if not nim or not nama or not jurusan or not tugas or not uts or not uas:
            flash('Tolong masukkan data dengan benar!')
        else:
            conn = dbconnect()
            conn.execute('INSERT INTO mhs (NIM, NAMA, JURUSAN) VALUES (?, ?, ?)',
                         (nim, nama, jurusan))
            total = int(tugas) + int(uts) + int(uas)
            rata = total / 3
            status, grade = hitnilstat(rata)
            conn.execute('INSERT INTO lnilai (NIM, TUGAS, UTS, UAS, TOTAL, RATA, STATUS, GRADE) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                         (nim, tugas, uts, uas, total, rata, status, grade))
            conn.commit()
            conn.close()
            return redirect(url_for('students'))

    return render_template('add.html')


@app.route('/students')
def students():
    search = request.args.get('search')
    conn = dbconnect()

    if search:
        query = '''
            SELECT mhs.NIM, mhs.NAMA, mhs.JURUSAN, lnilai.STATUS
            FROM mhs
            LEFT JOIN lnilai ON mhs.NIM = lnilai.NIM
            WHERE mhs.NIM LIKE ? OR mhs.NAMA LIKE ? OR mhs.JURUSAN LIKE ?
        '''
        search = f'%{search}%'
        students_grades = conn.execute(query, (search, search, search)).fetchall()
    else:
        query = '''
            SELECT mhs.NIM, mhs.NAMA, mhs.JURUSAN, lnilai.STATUS
            FROM mhs
            LEFT JOIN lnilai ON mhs.NIM = lnilai.NIM
        '''
        students_grades = conn.execute(query).fetchall()

    conn.close()
    return render_template('students.html', students_grades=students_grades)


@app.route('/view_grades/<nim>')
def view_grades(nim):
    conn = dbconnect()
    student = conn.execute('''
        SELECT mhs.NIM, mhs.NAMA, mhs.JURUSAN, lnilai.TUGAS, lnilai.UTS, lnilai.UAS, lnilai.TOTAL, lnilai.RATA, lnilai.STATUS, lnilai.GRADE
        FROM mhs
        LEFT JOIN lnilai ON mhs.NIM = lnilai.NIM
        WHERE mhs.NIM = ?
    ''', (nim,)).fetchone()
    conn.close()
    return render_template('view_grades.html', student=student)


@app.route('/edit/<nim>', methods=('GET', 'POST'))
def edit(nim):
    conn = dbconnect()
    student = conn.execute('''
        SELECT mhs.NIM, mhs.NAMA, mhs.JURUSAN, lnilai.TUGAS, lnilai.UTS, lnilai.UAS, lnilai.TOTAL, lnilai.RATA, lnilai.STATUS, lnilai.GRADE
        FROM mhs
        LEFT JOIN lnilai ON mhs.NIM = lnilai.NIM
        WHERE mhs.NIM = ?
    ''', (nim,)).fetchone()

    if request.method == 'POST':
        nama = request.form['nama']
        jurusan = request.form['jurusan']
        tugas = request.form['tugas']
        uts = request.form['uts']
        uas = request.form['uas']

        if not nama or not jurusan or not tugas or not uts or not uas:
            flash('Please fill in all fields!')
        else:
            total = int(tugas) + int(uts) + int(uas)
            rata = total / 3
            status, grade = hitnilstat(rata)

            conn.execute('UPDATE mhs SET NAMA = ?, JURUSAN = ? WHERE NIM = ?',
                         (nama, jurusan, nim))
            existing_record = conn.execute('SELECT * FROM lnilai WHERE NIM = ?', (nim,)).fetchone()
            if existing_record:
                conn.execute('''
                    UPDATE lnilai SET TUGAS = ?, UTS = ?, UAS = ?, TOTAL = ?, RATA = ?, STATUS = ?, GRADE = ?
                    WHERE NIM = ?
                ''', (tugas, uts, uas, total, rata, status, grade, nim))
            else:
                conn.execute('''
                    INSERT INTO lnilai (NIM, TUGAS, UTS, UAS, TOTAL, RATA, STATUS, GRADE)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (nim, tugas, uts, uas, total, rata, status, grade))
            conn.commit()
            conn.close()
            return redirect(url_for('view_grades', nim=nim))

    conn.close()
    return render_template('edit.html', student=student)


@app.route('/delete/<nim>', methods=('POST',))
def delete(nim):
    conn = dbconnect()
    conn.execute('DELETE FROM mhs WHERE NIM = ?', (nim,))
    conn.execute('DELETE FROM lnilai WHERE NIM = ?', (nim,))
    conn.commit()
    conn.close()
    return redirect(url_for('students'))


if __name__ == '__main__':
    app.run()
