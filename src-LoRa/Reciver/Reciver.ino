/*The sender and receiver programs use the LoRa protocol with parameters such as operating frequency, bandwidth, spreading factor, coding rate, and transmission power configured for 
communication between the two Heltec ESP32 LoRa modules. The sender continuously transmits LoRa packets, while the receiver listens for incoming packets using the LoRa library. 
Although information about the received packet is available, this project is primarily interested in the received signal strength indicator (RSSI), measured in dBm. 
After receiving a packet, the receiver obtains its RSSI value and uses Serial.print(rssi) to transmit that value through serial communication to the Raspberry Pi. 
The Raspberry Pi then reads these RSSI measurements and uses them during the autonomous search and signal-source estimation process. */


#include "LoRaWan_APP.h"
#include "Arduino.h"


#define RF_FREQUENCY                                915000000 // Hz

#define TX_OUTPUT_POWER                             5        // dBm

#define LORA_BANDWIDTH                              0         
                                                              
#define LORA_SPREADING_FACTOR                       7         
#define LORA_CODINGRATE                             1         
                                                            
#define LORA_PREAMBLE_LENGTH                        8         
#define LORA_SYMBOL_TIMEOUT                         0       
#define LORA_FIX_LENGTH_PAYLOAD_ON                  false
#define LORA_IQ_INVERSION_ON                        false


#define RX_TIMEOUT_VALUE                            1000
#define BUFFER_SIZE                                 30 

char rxpacket[BUFFER_SIZE];

static RadioEvents_t RadioEvents;

int16_t txNumber;

int16_t rssi,rxSize;

bool lora_idle = true;

void setup() {
    Serial.begin(115200);  

    while(!Serial){}


    
    Mcu.begin(HELTEC_BOARD,SLOW_CLK_TPYE);
    
    txNumber=0;
    rssi=0;
  
    RadioEvents.RxDone = OnRxDone;
    Radio.Init( &RadioEvents );
    Radio.SetChannel( RF_FREQUENCY );
    Radio.SetRxConfig( MODEM_LORA, LORA_BANDWIDTH, LORA_SPREADING_FACTOR,
                               LORA_CODINGRATE, 0, LORA_PREAMBLE_LENGTH,
                               LORA_SYMBOL_TIMEOUT, LORA_FIX_LENGTH_PAYLOAD_ON,
                               0, true, 0, 0, LORA_IQ_INVERSION_ON, true );
}



void loop()
{
  if(lora_idle)
  {
    lora_idle = false;
    Radio.Rx(0);
  }
  Radio.IrqProcess( );
}

void OnRxDone( uint8_t *payload, uint16_t size, int16_t rssi, int8_t snr )
{
    rssi=rssi;
    rxSize=size;
    memcpy(rxpacket, payload, size );
    rxpacket[size]='\0';
    Radio.Sleep( );
    lora_idle = true;
    Serial.println(rssi); // This sends it to the serail port of Raspberry Pi so the raspberry can get the RSSI value.
    delay(1);
}
