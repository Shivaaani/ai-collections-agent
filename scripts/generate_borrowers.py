"""Generate the 20 synthetic borrower profiles in data/borrowers.json.

Every value is made up. Due dates are stored as days past due (DPD) and turned
into calendar dates at load time, so the data never ages out of the 1-30 DPD bucket.
"""

import json
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "borrowers.json"

PEOPLE = [
    ("Aarav Sharma", "Pune"),
    ("Priya Nair", "Kochi"),
    ("Rohan Mehta", "Mumbai"),
    ("Ananya Iyer", "Chennai"),
    ("Vikram Singh", "Jaipur"),
    ("Sneha Patil", "Nagpur"),
    ("Arjun Reddy", "Hyderabad"),
    ("Kavya Menon", "Bengaluru"),
    ("Rahul Verma", "Lucknow"),
    ("Pooja Gupta", "Delhi"),
    ("Siddharth Joshi", "Ahmedabad"),
    ("Meera Pillai", "Thiruvananthapuram"),
    ("Karan Malhotra", "Chandigarh"),
    ("Divya Rao", "Mysuru"),
    ("Imran Khan", "Bhopal"),
    ("Neha Kulkarni", "Nashik"),
    ("Aditya Banerjee", "Kolkata"),
    ("Fatima Sheikh", "Indore"),
    ("Manish Yadav", "Patna"),
    ("Ritu Chauhan", "Dubai"),  # works abroad: tests the calling-hours check in another timezone
]

LOAN_SIZES = [50_000, 75_000, 1_00_000, 1_50_000, 2_00_000, 3_00_000, 4_00_000, 5_00_000]
TENURES_MONTHS = [12, 18, 24, 36]
ANNUAL_RATE = 0.18
LATE_FEE = 500


def emi(principal: int, months: int, annual_rate: float = ANNUAL_RATE) -> int:
    r = annual_rate / 12
    return round(principal * r * (1 + r) ** months / ((1 + r) ** months - 1))


def pan(rng: random.Random, surname: str) -> str:
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return (
        "".join(rng.choice(letters) for _ in range(3))
        + "P"
        + surname[0].upper()
        + f"{rng.randint(1000, 9999)}"
        + rng.choice(letters)
    )


def main() -> None:
    rng = random.Random(42)
    borrowers = []
    for i, (name, city) in enumerate(PEOPLE, start=1):
        principal = rng.choice(LOAN_SIZES)
        tenure = rng.choice(TENURES_MONTHS)
        monthly = emi(principal, tenure)
        dpd = rng.randint(1, 30)
        borrowers.append(
            {
                "borrower_id": f"B{i:03d}",
                "name": name,
                "dob": f"{rng.randint(1975, 2000)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
                "phone": f"+91 9{rng.randint(100000000, 999999999)}",
                "pan": pan(rng, name.split()[-1]),
                "loan_id": f"SFL-PL-{rng.randint(100000, 999999)}",
                "city": city,
                "timezone": "Asia/Dubai" if city == "Dubai" else "Asia/Kolkata",
                "preferred_language": rng.choice(["en", "en", "hinglish"]),
                "loan_amount": principal,
                "tenure_months": tenure,
                "emi_amount": monthly,
                "days_past_due": dpd,
                "late_fee": LATE_FEE if dpd > 3 else 0,
                "broken_promises_last_6m": rng.choice([0, 0, 0, 1, 2]),
                "restructure_eligible": principal >= 1_00_000 and tenure <= 24,
            }
        )
    OUT.write_text(json.dumps(borrowers, indent=2) + "\n")
    print(f"Wrote {len(borrowers)} borrowers to {OUT}")


if __name__ == "__main__":
    main()
