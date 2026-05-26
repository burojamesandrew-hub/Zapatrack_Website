import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status as drf_status
from .db import query, get_conn, release_conn
from psycopg2.extras import RealDictCursor

PICKUP_TIME_SLOTS = ['8:00 AM – 9:00 AM','9:00 AM – 10:00 AM','10:00 AM – 11:00 AM','1:00 PM – 2:00 PM','2:00 PM – 3:00 PM','3:00 PM – 4:00 PM']

@api_view(['GET', 'HEAD'])
def health_check(request):
    """Check if server and database are running."""
    try:
        # Test database connection
        row = query('SELECT 1 as health')
        if row is None:
            return Response({'status': 'degraded', 'message': 'Database connection issue'}, status=drf_status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({'status': 'ok', 'message': 'Server and database are operational'})
    except Exception as e:
        return Response({'status': 'error', 'message': f'Health check failed: {str(e)}'}, status=drf_status.HTTP_503_SERVICE_UNAVAILABLE)

def _s(row):
    """Safely serialize a database row to dict, converting datetime and UUID objects."""
    if row is None: 
        return None
    try:
        d = dict(row)
        for k, v in d.items():
            if hasattr(v, 'isoformat'): 
                d[k] = v.isoformat()
            elif type(v).__name__ == 'UUID': 
                d[k] = str(v)
        return d
    except Exception as e:
        print(f'[API] Error serializing row: {e}')
        raise RuntimeError(f'Data serialization error: {str(e)}')

def _sm(rows): 
    """Safely serialize multiple rows."""
    if not rows:
        return []
    try:
        return [_s(r) for r in rows]
    except Exception as e:
        print(f'[API] Error serializing rows: {e}')
        raise RuntimeError(f'Data serialization error: {str(e)}')

@api_view(['GET'])
def get_status(request, request_id):

    row = query("SELECT request_id,request_id_text,resident_name,cert_type,status,purpose,date_requested,pickup_date,pickup_time_slot,pickup_status FROM v_requests_overview WHERE request_id_text=%s",(str(request_id).strip(),))
    if not row: return Response({'error':'Request not found. Please check your Request ID.'},status=drf_status.HTTP_404_NOT_FOUND)
    return Response(_s(row))

    try:
        rid = str(request_id).strip()
        print(f'[API] get_status called with request_id={rid}')
        row = query(
            "SELECT request_id, resident_name, cert_type, status, purpose, "
            "date_requested, pickup_date, pickup_time_slot "
            "FROM v_resident_status WHERE request_id::TEXT=%s",
            (rid,)
        )
        if not row: 
            return Response({'error':'Request not found. Please check your Request ID or try the QR code scanner.'},status=drf_status.HTTP_404_NOT_FOUND)
        return Response(_s(row))
    except Exception as e:
        print(f'[API] get_status error: {e}')
        import traceback
        traceback.print_exc()
        return Response({'error': f'Server error: {str(e)}. Please contact the barangay office for assistance.'}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)
      

@api_view(['GET'])
def list_requests(request):
    try:
        sf=request.GET.get('status',''); cf=request.GET.get('cert_type',''); search=request.GET.get('search','').strip().lower()
        page=max(int(request.GET.get('page',1)),1); ps=int(request.GET.get('page_size',10)); offset=(page-1)*ps
        sql="SELECT request_id,request_id_text,resident_name,cert_type,status,date_requested,purpose,encoded_by FROM v_requests_overview WHERE 1=1"
        params=[]
        if sf: sql+=' AND status=%s'; params.append(sf)
        if cf: sql+=' AND cert_type=%s'; params.append(cf)
        if search: sql+=' AND (LOWER(resident_name) LIKE %s OR LOWER(request_id_text) LIKE %s)'; params.extend([f'%{search}%',f'%{search}%'])
        cnt=query(f'SELECT COUNT(*) AS cnt FROM ({sql}) sub',params); total=cnt['cnt'] if cnt else 0
        sql+=' ORDER BY submitted_at DESC LIMIT %s OFFSET %s'; params.extend([ps,offset])
        rows=query(sql,params,many=True)
        return Response({'total':total,'page':page,'page_size':ps,'results':_sm(rows)})
    except Exception as e:
        print(f'[API] list_requests error: {e}')
        return Response({'error': f'Server error: Unable to retrieve requests. {str(e)}'}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_request(request, request_id):
    try:
        rid = str(request_id).strip()
        if not rid:
            return Response({'error': 'Request ID cannot be empty'}, status=drf_status.HTTP_400_BAD_REQUEST)
        row = query(
            'SELECT r.* FROM v_requests_overview r LEFT JOIN qr_codes q ON q.request_id = r.request_id WHERE r.request_id_text=%s OR q.qr_data=%s',
            (rid, rid),
        )
        if not row: 
            return Response({'error':'Request not found. Please verify the Request ID or QR code and try again.'},status=drf_status.HTTP_404_NOT_FOUND)
        data=_s(row); ct=data.get('cert_type',''); rid=str(row['request_id'])
        if ct=='Barangay Clearance':
            detail=query("SELECT purpose,id_type_presented,id_number,with_community_tax,ctc_number,ctc_date_issued,fee_amount,remarks FROM clearance_details WHERE request_id=%s",(rid,)); data['detail']=_s(detail)
        elif ct=='Certificate of Indigency':
            detail=query("SELECT reason,monthly_income,num_dependents,for_medical,for_scholarship,for_burial,for_legal_aid,for_government_aid,beneficiary_name,beneficiary_relation,requesting_institution FROM indigency_details WHERE request_id=%s",(rid,)); data['detail']=_s(detail)
        elif ct=='Certificate of Residency':
            detail=query("SELECT purpose,years_of_residency,months_of_residency,born_in_barangay,previous_address,requested_for,requested_for_relation,for_enrollment,for_employment,for_voter_reg,for_bank,for_utility,requesting_institution FROM residency_details WHERE request_id=%s",(rid,)); data['detail']=_s(detail)
        logs=query(
            "SELECT sl.old_status, sl.new_status, sl.notes, sl.changed_at, "
            "COALESCE(s.full_name, 'System') AS changed_by "
            "FROM status_logs sl "
            "LEFT JOIN staff s ON s.id = sl.changed_by "
            "WHERE sl.request_id=%s "
            "ORDER BY sl.changed_at ASC",
            (rid,),
            many=True
        )
        data['status_log']=_sm(logs)
        qr=query('SELECT qr_data,image_path FROM qr_codes WHERE request_id=%s',(rid,)); data['qr']=_s(qr)
        return Response(data)
    except Exception as e:
        print(f'[API] get_request error: {e}')
        return Response({'error': f'Server error: Unable to retrieve request details. {str(e)}'}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_summary(request):
    try:
        row=query('SELECT * FROM v_status_summary')
        return Response(_s(row) or {})
    except Exception as e:
        print(f'[API] get_summary error: {e}')
        return Response({'error': f'Server error: Unable to retrieve summary. {str(e)}'}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_appointment(request, request_id):
    try:
        row=query("SELECT ap.id,ap.pickup_date,ap.pickup_time_slot,ap.pickup_status,ap.created_at,ap.updated_at FROM appointments ap JOIN certificate_requests cr ON cr.id=ap.request_id WHERE cr.id::TEXT=%s",(str(request_id).strip(),))
        return Response({'appointment':_s(row)})
    except Exception as e:
        print(f'[API] get_appointment error: {e}')
        return Response({'error': f'Server error: Unable to retrieve appointment. {str(e)}'}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def create_appointment(request):
    try:
        data=request.data; rid=data.get('request_id','').strip(); pd=data.get('pickup_date','').strip(); ps=data.get('pickup_time_slot','').strip()
        if not all([rid,pd,ps]): return Response({'error':'request_id, pickup_date, and pickup_time_slot are required.'},status=drf_status.HTTP_400_BAD_REQUEST)
        if ps not in PICKUP_TIME_SLOTS: return Response({'error':f'Invalid time slot. Available slots: {", ".join(PICKUP_TIME_SLOTS)}'},status=drf_status.HTTP_400_BAD_REQUEST)
        req_row=query("SELECT id,status FROM certificate_requests WHERE id::TEXT=%s",(rid,))
        if not req_row: return Response({'error':'Request not found.'},status=drf_status.HTTP_404_NOT_FOUND)
        if req_row['status']!='Ready for Pickup': return Response({'error':f'Cannot schedule appointment. Current status: "{req_row["status"]}", required status: "Ready for Pickup".'},status=drf_status.HTTP_400_BAD_REQUEST)
        existing=query('SELECT id FROM appointments WHERE request_id=%s',(str(req_row['id']),))
        if existing: return Response({'error':'An appointment is already scheduled for this request.'},status=drf_status.HTTP_409_CONFLICT)
        conn=get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("INSERT INTO appointments (request_id,pickup_date,pickup_time_slot) VALUES (%s,%s,%s) RETURNING id",(str(req_row['id']),pd,ps)); new_id=cur.fetchone()['id']; conn.commit()
            return Response({'success':True,'appointment_id':str(new_id)},status=drf_status.HTTP_201_CREATED)
        except Exception as e:
            conn.rollback(); return Response({'error':f'Failed to create appointment: {str(e)}'},status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally: release_conn(conn)
    except Exception as e:
        print(f'[API] create_appointment error: {e}')
        return Response({'error': f'Server error: Unable to create appointment. {str(e)}'}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_timeslots(request):
    return Response({'slots':PICKUP_TIME_SLOTS})

@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def api_not_found(request, path=None):
    return Response(
        {'error': 'API endpoint not found. Please verify the request path under /api/.'},
        status=drf_status.HTTP_404_NOT_FOUND,
    )

def handler404(request, exception=None):
    from django.http import JsonResponse
    return JsonResponse(
        {'error': 'Page or API endpoint not found.'},
        status=404,
    )

def handler500(request):
    from django.http import JsonResponse
    return JsonResponse(
        {'error': 'Internal server error. Please contact the barangay office.'},
        status=500,
    )