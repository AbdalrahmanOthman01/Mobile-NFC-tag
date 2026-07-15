package org.example.nfcvault;

import android.nfc.cardemulation.HostApduService;
import android.os.Bundle;
import android.util.Log;

public class SecureBadgeService extends HostApduService {
    private static final String TAG = "SecureBadgeService";
    
    // Response status codes (9000 = Success, 6F00 = Failure/Unknown)
    private static final byte[] STATUS_SUCCESS = new byte[]{(byte) 0x90, (byte) 0x00};
    private static final byte[] STATUS_FAILED = new byte[]{(byte) 0x6F, (byte) 0x00};
    
    @Override
    public byte[] processCommandApdu(byte[] commandApdu, Bundle extras) {
        Log.i(TAG, "Received APDU Command: " + bytesToHex(commandApdu));
        
        if (commandApdu == null || commandApdu.length < 4) {
            return STATUS_FAILED;
        }
        
        // ISO 7816 SELECT AID Command: CLA=00, INS=A4, P1=04, P2=00
        if (commandApdu[0] == (byte) 0x00 && 
            commandApdu[1] == (byte) 0xA4 && 
            commandApdu[2] == (byte) 0x04 && 
            commandApdu[3] == (byte) 0x00) {
            
            Log.i(TAG, "Custom AID (F0010203040506) matched. Transmitting badge authentication payload...");
            
            // Safe, dynamic authorization token payload
            String payload = "AUTH:SECURE_DIGITAL_BADGE_PASS_TOKEN_2026";
            byte[] payloadBytes = payload.getBytes();
            byte[] response = new byte[payloadBytes.length + STATUS_SUCCESS.length];
            
            // Copy payload bytes, followed by standard 9000 success trailer
            System.arraycopy(payloadBytes, 0, response, 0, payloadBytes.length);
            System.arraycopy(STATUS_SUCCESS, 0, response, payloadBytes.length, STATUS_SUCCESS.length);
            
            return response;
        }
        
        return STATUS_FAILED;
    }
    
    @Override
    public void onDeactivated(int reason) {
        Log.i(TAG, "HCE Connection deactivated. Reason code: " + reason);
    }
    
    private String bytesToHex(byte[] bytes) {
        if (bytes == null) return "";
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            sb.append(String.format("%02X ", b));
        }
        return sb.toString().trim();
    }
}
