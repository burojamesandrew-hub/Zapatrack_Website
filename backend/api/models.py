"""
models.py — Barangay Zapatera Certificate Information System
Django ORM models mapped from the PostgreSQL schema (v2).

Design notes
------------
* All primary keys are UUIDs (PostgreSQL gen_random_uuid() → Python uuid.uuid4).
* PostgreSQL ENUMs are replicated as Django TextChoices so they stay in sync
  with the DB type while giving you Python-level validation.
* The schema uses three per-cert-type detail tables (clearance_details,
  indigency_details, residency_details).  Each maps to a OneToOneField back
  to CertificateRequest.
* updated_at columns that are maintained by PostgreSQL triggers are declared
  with editable=False so Django never tries to set them from Python.
* The Staff model is intentionally separate from Django's built-in User model
  because auth is handled by the desktop app (bcrypt hashes).  If you later
  want Django auth for the web portal, subclass AbstractBaseUser instead.
* Meta.managed = True on all models (default) — Django's migrations will
  manage the schema.  If you want Django to skip DDL for tables already
  created by the SQL script, set managed = False on each model.
"""

import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# ---------------------------------------------------------------------------
#  CHOICES  (mirrors PostgreSQL ENUMs)
# ---------------------------------------------------------------------------

class RequestStatus(models.TextChoices):
    PENDING         = "Pending",         "Pending"
    APPROVED        = "Approved",        "Approved"
    READY_FOR_PICKUP = "Ready for Pickup", "Ready for Pickup"
    CLAIMED         = "Claimed",         "Claimed"
    REJECTED        = "Rejected",        "Rejected"
    CANCELLED       = "Cancelled",       "Cancelled"


class CertType(models.TextChoices):
    BARANGAY_CLEARANCE      = "Barangay Clearance",       "Barangay Clearance"
    CERTIFICATE_OF_INDIGENCY = "Certificate of Indigency", "Certificate of Indigency"
    CERTIFICATE_OF_RESIDENCY = "Certificate of Residency", "Certificate of Residency"


class CivilStatus(models.TextChoices):
    SINGLE            = "Single",            "Single"
    MARRIED           = "Married",           "Married"
    WIDOWED           = "Widowed",           "Widowed"
    LEGALLY_SEPARATED = "Legally Separated", "Legally Separated"


class Gender(models.TextChoices):
    MALE             = "Male",              "Male"
    FEMALE           = "Female",            "Female"
    PREFER_NOT_TO_SAY = "Prefer not to say", "Prefer not to say"


class StaffRole(models.TextChoices):
    ADMIN     = "Admin",     "Admin"
    SECRETARY = "Secretary", "Secretary"
    ENCODER   = "Encoder",   "Encoder"


class PickupStatus(models.TextChoices):
    SCHEDULED   = "Scheduled",   "Scheduled"
    COMPLETED   = "Completed",   "Completed"
    NO_SHOW     = "No Show",     "No Show"
    RESCHEDULED = "Rescheduled", "Rescheduled"
    CANCELLED   = "Cancelled",   "Cancelled"


# ---------------------------------------------------------------------------
#  RESIDENTS
# ---------------------------------------------------------------------------

class Resident(models.Model):
    """
    Walk-in residents who file certificate requests.
    One resident can have multiple certificate requests over time.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    full_name = models.CharField(max_length=150)
    date_of_birth = models.DateField()
    age = models.SmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(129)],
        help_text="Snapshot age at time of registration; should correspond to date_of_birth.",
    )
    civil_status = models.CharField(
        max_length=20,
        choices=CivilStatus.choices,
    )
    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
    )
    address = models.TextField()
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    nationality = models.CharField(max_length=80, default="Filipino")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(
        editable=False,
        auto_now=True,
        help_text="Maintained by PostgreSQL trigger trg_residents_updated_at.",
    )

    class Meta:
        db_table = "residents"
        managed = False
        ordering = ["-created_at"]
        indexes = [
            # mirrors idx_residents_full_name (case-insensitive; define via migration)
            models.Index(fields=["full_name"], name="idx_residents_full_name"),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.id})"


# ---------------------------------------------------------------------------
#  STAFF
# ---------------------------------------------------------------------------

class Staff(models.Model):
    """
    Barangay staff who operate the desktop application.
    Passwords are stored as bcrypt hashes — never plain text.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    full_name = models.CharField(max_length=150)
    username = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(
        max_length=255,
        help_text="bcrypt hash only — never store plain text.",
    )
    role = models.CharField(
        max_length=20,
        choices=StaffRole.choices,
        default=StaffRole.ENCODER,
        help_text=(
            "Admin: full access. "
            "Secretary: process + generate. "
            "Encoder: new requests only."
        ),
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "staff"
        managed = False
        verbose_name = "Staff Member"
        verbose_name_plural = "Staff Members"

    def __str__(self):
        return f"{self.full_name} [{self.get_role_display()}]"


# ---------------------------------------------------------------------------
#  CERTIFICATE REQUESTS  (base table — shared fields for all cert types)
# ---------------------------------------------------------------------------

class CertificateRequest(models.Model):
    """
    One row per request.  The UUID `id` is printed on the claim stub
    and encoded into the QR code scanned by the web portal.

    The cert_type field determines which detail table
    (ClearanceDetail / IndigencyDetail / ResidencyDetail)
    holds the cert-specific data.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    resident = models.ForeignKey(
        Resident,
        on_delete=models.RESTRICT,
        related_name="certificate_requests",
    )
    encoded_by = models.ForeignKey(
        Staff,
        on_delete=models.RESTRICT,
        related_name="encoded_requests",
    )
    cert_type = models.CharField(
        max_length=40,
        choices=CertType.choices,
        help_text="Determines which detail table (clearance/indigency/residency) has the matching row.",
    )
    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING,
    )
    or_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Official Receipt number if a processing fee was collected.",
    )
    date_requested = models.DateField(auto_now_add=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(
        editable=False,
        auto_now=True,
        help_text="Maintained by PostgreSQL trigger trg_requests_updated_at.",
    )

    class Meta:
        db_table = "certificate_requests"
        managed = False   
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(fields=["status"],      name="idx_requests_status"),
            models.Index(fields=["resident"],    name="idx_requests_resident_id"),
            models.Index(fields=["cert_type"],   name="idx_requests_cert_type"),
            models.Index(fields=["-submitted_at"], name="idx_requests_submitted_at"),
        ]

    def __str__(self):
        return f"{self.cert_type} — {self.resident.full_name} [{self.status}]"

    # ------------------------------------------------------------------
    #  Convenience accessors — return the matching detail object or None
    # ------------------------------------------------------------------

    @property
    def detail(self):
        """Return whichever detail object matches cert_type, or None."""
        if self.cert_type == CertType.BARANGAY_CLEARANCE:
            return getattr(self, "clearance_detail", None)
        if self.cert_type == CertType.CERTIFICATE_OF_INDIGENCY:
            return getattr(self, "indigency_detail", None)
        if self.cert_type == CertType.CERTIFICATE_OF_RESIDENCY:
            return getattr(self, "residency_detail", None)
        return None

    @property
    def purpose(self):
        """Mirrors COALESCE(cd.purpose, id.reason, rd.purpose) from v_resident_status."""
        d = self.detail
        if d is None:
            return None
        return getattr(d, "purpose", None) or getattr(d, "reason", None)


# ---------------------------------------------------------------------------
#  CERTIFICATE-TYPE DETAIL TABLES
# ---------------------------------------------------------------------------

class ClearanceDetail(models.Model):
    """
    Fields specific to 'Barangay Clearance' requests.
    Use cases: employment, business permit, NBI clearance, travel, etc.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    request = models.OneToOneField(
        CertificateRequest,
        on_delete=models.CASCADE,
        related_name="clearance_detail",
        db_column="request_id",
    )

    # Purpose / intended use
    purpose = models.TextField()

    # Valid ID presented at the counter
    id_type_presented = models.CharField(
        max_length=80,
        help_text="e.g. 'PhilSys ID', 'Voter's ID', 'Passport'.",
    )
    id_number = models.CharField(
        max_length=80,
        blank=True,
        null=True,
        help_text="ID number (optional if staff records visually).",
    )

    # Community Tax Certificate (Cedula)
    with_community_tax = models.BooleanField(
        default=False,
        help_text="TRUE if the resident presented a Community Tax Certificate (Cedula).",
    )
    ctc_number = models.CharField(max_length=30, blank=True, null=True)
    ctc_date_issued = models.DateField(blank=True, null=True)
    ctc_place_issued = models.CharField(max_length=100, blank=True, null=True)

    # Fee
    fee_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
    )

    # Additional remarks
    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "clearance_details"
        managed = False
        indexes = [
            models.Index(fields=["request"], name="idx_clearance_request_id"),
        ]
        constraints = [
            # mirrors chk_ctc_complete
            models.CheckConstraint(
                condition=(
                    models.Q(with_community_tax=False)
                    | (
                        models.Q(ctc_number__isnull=False)
                        & models.Q(ctc_date_issued__isnull=False)
                        & models.Q(ctc_place_issued__isnull=False)
                    )
                ),
                name="chk_ctc_complete",
            ),
        ]

    def __str__(self):
        return f"ClearanceDetail for request {self.request_id}"


class IndigencyDetail(models.Model):
    """
    Fields specific to 'Certificate of Indigency' requests.
    Use cases: medical assistance, scholarship, burial, legal aid, DSWD/Philhealth.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    request = models.OneToOneField(
        CertificateRequest,
        on_delete=models.CASCADE,
        related_name="indigency_detail",
        db_column="request_id",
    )

    # Reason for the certificate
    reason = models.TextField()

    # Household financial info
    monthly_income = models.CharField(
        max_length=50,
        default="Below minimum wage",
        help_text="Descriptive income range (e.g. 'Below minimum wage'). Not an exact figure.",
    )
    num_dependents = models.SmallIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of dependents in the household.",
    )

    # Purpose checkboxes
    for_medical       = models.BooleanField(default=False)
    for_scholarship   = models.BooleanField(default=False)
    for_burial        = models.BooleanField(default=False)
    for_legal_aid     = models.BooleanField(default=False)
    for_government_aid = models.BooleanField(
        default=False,
        help_text="DSWD, 4Ps, etc.",
    )
    for_other         = models.BooleanField(default=False)
    other_purpose_details = models.TextField(
        blank=True,
        null=True,
        help_text="Required when for_other = TRUE.",
    )

    # Beneficiary
    beneficiary_name     = models.CharField(max_length=150, blank=True, null=True)
    beneficiary_relation = models.CharField(
        max_length=80,
        blank=True,
        null=True,
        help_text="e.g. 'Self', 'Daughter', 'Son'.",
    )

    # Referring office / institution
    requesting_institution = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="e.g. 'Cebu City Medical Center', 'UST'.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "indigency_details"
        managed = False
        indexes = [
            models.Index(fields=["request"], name="idx_indigency_request_id"),
        ]
        constraints = [
            # mirrors chk_other_purpose
            models.CheckConstraint(
                condition=(
                    models.Q(for_other=False)
                    | models.Q(other_purpose_details__isnull=False)
                ),
                name="chk_other_purpose",
            ),
            # mirrors chk_at_least_one_purpose
            models.CheckConstraint(
                condition=(
                    models.Q(for_medical=True)
                    | models.Q(for_scholarship=True)
                    | models.Q(for_burial=True)
                    | models.Q(for_legal_aid=True)
                    | models.Q(for_government_aid=True)
                    | models.Q(for_other=True)
                ),
                name="chk_at_least_one_purpose",
            ),
        ]

    def __str__(self):
        return f"IndigencyDetail for request {self.request_id}"


class ResidencyDetail(models.Model):
    """
    Fields specific to 'Certificate of Residency' requests.
    Use cases: school enrollment, voter registration, bank account,
    utility connection, employment.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    request = models.OneToOneField(
        CertificateRequest,
        on_delete=models.CASCADE,
        related_name="residency_detail",
        db_column="request_id",
    )

    # Purpose
    purpose = models.TextField()

    # Length of residency
    years_of_residency = models.SmallIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Full years the resident has lived in Brgy. Zapatera.",
    )
    months_of_residency = models.SmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(11)],
        help_text="Additional months on top of years_of_residency (0–11).",
    )

    # Previous address
    previous_address  = models.TextField(
        blank=True,
        null=True,
        help_text="NULL if born/raised in the barangay.",
    )
    born_in_barangay  = models.BooleanField(
        default=False,
        help_text="TRUE if the resident was born in Brgy. Zapatera and has always lived here.",
    )

    # Who the certificate is for
    requested_for = models.CharField(
        max_length=150,
        default="Self",
        help_text="Whose residency is being certified — usually 'Self' but may be a minor child.",
    )
    requested_for_relation = models.CharField(
        max_length=80,
        blank=True,
        null=True,
        help_text="e.g. 'Self', 'Child', 'Spouse'.",
    )

    # Purpose checkboxes
    for_enrollment  = models.BooleanField(default=False)
    for_employment  = models.BooleanField(default=False)
    for_voter_reg   = models.BooleanField(default=False)
    for_bank        = models.BooleanField(default=False)
    for_utility     = models.BooleanField(default=False)
    for_other       = models.BooleanField(default=False)
    other_purpose_details = models.TextField(
        blank=True,
        null=True,
        help_text="Required when for_other = TRUE.",
    )

    # Requesting institution
    requesting_institution = models.CharField(max_length=200, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "residency_details"
        managed = False
        indexes = [
            models.Index(fields=["request"], name="idx_residency_request_id"),
        ]
        constraints = [
            # mirrors chk_residency_other_purpose
            models.CheckConstraint(
                condition=(
                    models.Q(for_other=False)
                    | models.Q(other_purpose_details__isnull=False)
                ),
                name="chk_residency_other_purpose",
            ),
            # mirrors chk_residency_at_least_one_purpose
            models.CheckConstraint(
                condition=(
                    models.Q(for_enrollment=True)
                    | models.Q(for_employment=True)
                    | models.Q(for_voter_reg=True)
                    | models.Q(for_bank=True)
                    | models.Q(for_utility=True)
                    | models.Q(for_other=True)
                ),
                name="chk_residency_at_least_one_purpose",
            ),
        ]

    def __str__(self):
        return f"ResidencyDetail for request {self.request_id}"


# ---------------------------------------------------------------------------
#  SUPPORTING TABLES
# ---------------------------------------------------------------------------

class StatusLog(models.Model):
    """
    Immutable audit trail of every status change on a CertificateRequest.
    Written by the PostgreSQL trigger trg_log_status_change — do NOT
    insert manually from application code.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    request = models.ForeignKey(
        CertificateRequest,
        on_delete=models.CASCADE,
        related_name="status_logs",
        db_column="request_id",
    )
    changed_by = models.ForeignKey(
        Staff,
        on_delete=models.RESTRICT,
        related_name="status_changes",
        db_column="changed_by",
    )
    old_status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        blank=True,
        null=True,
        help_text="NULL when this is the initial creation entry for a new request.",
    )
    new_status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
    )
    notes = models.TextField(blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "status_logs"
        managed = False
        ordering = ["-changed_at"]
        indexes = [
            models.Index(
                fields=["request", "-changed_at"],
                name="idx_status_logs_request_id",
            ),
        ]

    def __str__(self):
        return (
            f"[{self.changed_at:%Y-%m-%d %H:%M}] "
            f"{self.old_status or 'NEW'} → {self.new_status} "
            f"(request {self.request_id})"
        )


class QRCode(models.Model):
    """
    One QR code per certificate request.
    qr_data stores the request UUID as text — this is what the QR image encodes.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    request = models.OneToOneField(
        CertificateRequest,
        on_delete=models.CASCADE,
        related_name="qr_code",
        db_column="request_id",
    )
    qr_data = models.TextField(
        help_text="The request UUID cast to text — this is what the QR image encodes.",
    )
    image_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="File path or URL to the PNG. NULL until the image has been saved.",
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "qr_codes"
        managed = False
    def __str__(self):
        return f"QRCode for request {self.request_id}"


class GeneratedCertificate(models.Model):
    """
    The rendered certificate document.
    Created only after status = 'Approved'.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    request = models.OneToOneField(
        CertificateRequest,
        on_delete=models.CASCADE,
        related_name="generated_certificate",
        db_column="request_id",
    )
    generated_by = models.ForeignKey(
        Staff,
        on_delete=models.RESTRICT,
        related_name="generated_certificates",
        db_column="generated_by",
    )
    cert_type = models.CharField(
        max_length=40,
        choices=CertType.choices,
    )
    cert_content = models.TextField(
        help_text="Full rendered certificate text/HTML ready for printing.",
    )
    is_printed = models.BooleanField(
        default=False,
        help_text="Set to TRUE when staff confirms the physical certificate was printed.",
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "generated_certificates"
        managed = False

    def __str__(self):
        return f"Certificate [{self.cert_type}] for request {self.request_id}"


class Appointment(models.Model):
    """
    Optional pickup scheduling via the web portal.
    One appointment per certificate request.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    request = models.OneToOneField(
        CertificateRequest,
        on_delete=models.CASCADE,
        related_name="appointment",
        db_column="request_id",
    )
    pickup_date = models.DateField()
    pickup_time_slot = models.CharField(
        max_length=30,
        help_text="e.g. '9:00 AM – 10:00 AM'.",
    )
    pickup_status = models.CharField(
        max_length=20,
        choices=PickupStatus.choices,
        default=PickupStatus.SCHEDULED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(
        editable=False,
        auto_now=True,
        help_text="Maintained by PostgreSQL trigger trg_appointments_updated_at.",
    )

    class Meta:
        db_table = "appointments"
        managed = False
        ordering = ["pickup_date"]
        indexes = [
            models.Index(fields=["pickup_date"], name="idx_appointments_pickup_date"),
        ]

    def __str__(self):
        return (
            f"Appointment {self.pickup_date} {self.pickup_time_slot} "
            f"[{self.pickup_status}] — request {self.request_id}"
        )