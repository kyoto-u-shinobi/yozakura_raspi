#include "MEMS.h"
#include "mbed.h"

MEMS::MEMS(PinName sda, PinName scl)
        : _mems(sda, scl) {

}

void MEMS::temp(float* dt) {
        
    char  I2C_rd[64]; // 生データ
    short  datr[16]; // 16点 温度データ（10倍整数）
    short  PTAT; // センサ内部PTAT温度データ（10倍整数）
//    double   dt[16]; // 16点 温度データ
    short   d_PTAT; // センサ内部PTAT温度データ
    int  i,j;
    int  itemp;
    
    //// measure
    _mems.start();
    _mems.write(D6T_addr);
    _mems.write(D6T_cmd);
    // Repeated Start condition
    _mems.read(D6T_addr,I2C_rd,35);
//        if(check_PEC(I2C_rd) == -1) continue; // error
    for(i=0,j=0;i<17;i++){
        itemp = (I2C_rd[j++] & 0xff);
        itemp += I2C_rd[j++] * 256;
        if(i == 0) PTAT = itemp;
        else datr[i-1] = itemp;
    }
    for(i=0;i<16;i++){
        dt[i] = 0.1 * datr[i];
    }
    d_PTAT = 0.1 * PTAT;
}
