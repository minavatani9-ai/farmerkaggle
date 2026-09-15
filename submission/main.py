"""EXP120 — small purchase-shortfall repair on the EXP119 agent.

Preserves worker routes and stored wheat. When an early livestock purchase has
an estimated cash shortfall of at most 50 coins, sell uncommitted non-wheat
stock before that purchase. Reserve the next 24 steps of planned fertilizer
pickups, retain the hiring order, and keep the existing final-day planner.

Only legal observations are used. No opponent IDs, seeds, external services,
or mutable cross-game state. A Kaggle leaderboard rating is not guaranteed.
Kaggle-derived projection mechanics: see LICENSE_KAGGLE.txt (Apache-2.0).
"""
import base64
import json
import zlib

_PRODUCTS = ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON',
             'EGG', 'MILK', 'WOOL', 'FERTILIZER')
_ANIMAL_STRUCTURE = {'COW': 'PASTURE', 'SHEEP': 'PASTURE', 'GOOSE': 'COOP'}
_PLAN = json.loads(zlib.decompress(base64.b85decode(
    'c-qZfO^+klar`fH?gLrHul8*;OYIIcyS<p{H6aTPL4ai#Fyw>mo8kZN?j~8Rs*H??e8mxbngN?1uii(#%*e>dKmE^#fBVbd|Mu6vfB2_Aefag`w{'
    'IU_9zOj0U;gu7|LgUI*Z=<QFMt1!zy9~@|Nr#icfbAd&%b_s`r)@v&mSH>oPIifeEoObzdZcu!?)v?FK@3sJ-z<3d3y!Fc{P6X<+c6G%l|%%NAb('
    'k*XN(|VN5^X9nxRhUjOp(m(M?ceEZC&r_<{v-d_Ic^Vj1C_dk>G`1aHB`0LxZ%trm~>9^^qU#Ii)r$7Am>-BfnZ(jvox<2mse?NSE`t`#LeD3F`p'
    'Fci7T|WCZvTw)Z53jHPeEjnC%ZG>Ya{T`I_4)Ic&;N4#dU@*6+pn{qy*zumVch4(pFHMm*r(&S=MUL4{qDEVUw-)W>lS<d?QLGi510Mec{GzBn|;'
    'gMlz#d6=_qG(_5g2B7&iBGCcDv0{`~pNA1+@$+3IVspXGK&L!LeI`NzS;&fmAjn`FH5$wpx>&!5P7DcXVY1Rj6<@x#MmJ~fxef_v%sG3=$=EWFz('
    '@5#mL%=Z)D*RKor%kwZ<$t(Hb($jU>55wM^Z5H?oZ{zy-{Q8`;|GkeD{ybRX$#iA5qo0rWr;lI%IV|062*c6=dqAv!+K%sgXfq$n@88}(9msM1^K'
    'lBtf0|A`oVoX(PEJgxcXj;zvw@#1Tzu2{(d0Jo!FHN_letK@zkT``*XHuWuYdabg!b_D)1x1|UWs5Ou9iKlmSvUWg=H+l%zD7NpARb?4LQl#)W`J'
    '&24*xQU`C*uvoSo8xp{anP6@l9XMW=7OU_#dPU+2RP%CviYr<-R9T(?#*yh83;=ss*TZ@iv`0E}cKRcO^^RtjS2S0LKRdCX7f4qFM{8-q^hf_5CX'
    'XI>6pOr1M;YG*wijzA#(uH3HyJ&O>ky{3DUGlqElewWD()Gg2UGJNtB_gAnYnlZ$#@-6+47O3hotxXbl79qu;-{xCUyh%i|2(=1-whCcnfz*crA6'
    '0bn2g)~oqzB6jt)i|4wL?pA3uRZG`2M{h8T_#ouA;(^LS|R;AW${99rln%-w(E`rB8|%V;`B)~XOqU|6HPxN(RmvK<zU9`huYm<=5s%K5cXI+Va@'
    'pl=or5#z}$g1c_R9e52HQsXPbE(W3h%{n|7PVh0`+su%r(9Gorzde8bc>3M(>(@V;t`Ql>VA;u$zky7SCBE3nnUx8rN?WPh{uzH$j7FqIxw)hGHf'
    'VK;;*Bu)yK}sPo6;=Q-f>`MdZlC=Tp!e7u!A{tP>Tm;dpy$)ErK7_4>NvJUjla6?8DBtT&4)kUU)hOFsHEM6tb0J*Dcz*8W(4B`Smn?28oZCuOAR'
    'Eg#Tgq>M~p6zTXNk$osME%AhBWm<RClEiNg&bkT2+xWqSd1T@f5fpUg2hrJkO-N9u0=xO4KVw~K#R{&(lFkaJR?F<)a>{&SP9|ywVty`9UYCA$K5'
    'zyeaMk9JdLThmPe2t5yzBPD2SL(^fkyxHGK{>8p&Ru!2V`6@&r_+<Vpu{|Zm2{w}>reH3pTi^oc;E2Ats(zy^a3JG_8oYRT}w0+WBT)3cxDu*X)Z'
    '>Wdr=YUV^?%O^&8`9<G>UDB09BVp<-NR_()yy3&$`?>=MjOZdlqF`KI=%pMNY_{>Ze*UA1fCoB9~D3>Di0eba*HnFb#IBlDhsT`V<F^>Acrd;Y8)'
    'LN@$!iTra5GidT6u-Ra-Ys^4g4v8DZUe~tg=#g-FQUnfcax(Uom3K~Y&Qp01nUUxzHE&%qtE-fBpy4lu&2@$+YDSd3j*d%FBWIiOk2IxR%t+gJv{'
    'F~x#lH$5$OE-70zmG7*C{O^rLkGh2~5U#5AW^}1}qq)3|5-J4`8Ze#=jiK*(a)=P{=}GAMbRKl7PiHm?PMefWd*ogk|U-4u=VS$4Gql%NJu~xnCP'
    '?+nGZ)p2pyBo7gIe76|vrqD~a{Nd2O2N`6FFefSTU%Syt_Irf`7m`q9m(`aMA)M(mCu-kr|$IUgY2M_=upv0bi%JQ!-VvJ7c9K{3-NUEaq>blf@7'
    'QPk|u;#P);2v1;GG(DFUYLA2&&zgjvsG5!Y{sME5oXnm5An<RKtV>#ZQU)fJ;YyhLMVeTMurajVS7i*t!-~_@!X#VB!s)VE}Rfafz-NNsql{8ESu'
    '2W+8Hk!*1Rl(kQ`n?mzu*Ye9m&f#Ta`2hVf+1|2A0^7%@k)RF0GNZb_(FbK>2~j;@`&xEoUUFD-$-HzOo=YBx7G)Sze&#>V9~{^1nyeAaa<b@xmr'
    'fI9%WUo0Wrz&WUMVk=;-f@^3Zf+MN)26q@i^NqO$<J*)CVF82#Cy8&nTZ#q3G>`hag@}Wb&~{wMzFZ$jm)x;M;8LgAuvWYSeZ6-6Dx5R$B!)44Og'
    'F=Ur`cniCDGD`kbnMo#!XpVp?Ta>I89mH<{R=-O+s3$TFT$AoocoiIV4uzN0j1fgCJB=5*!ziFm}-?WO+U3R@!N!dHb<pKM%3#@}H*+p;2r$p0tg'
    '%<Ir?@FisO*#TdTH{;Mye0VPBZ-z=kQROGZE{$M1@sY69J&KTXQVw<MxKD*BTg7782`k38ng&gKkP%v19dD%`07YDb-$t^_Pa4r>L6>PklxKPV*-'
    'SdvW8@#USO&BW_7iTJI7~=UtyXub*TPg0TrpP{bc{h4r4-1D}bStcG^=;ME+vRqT+D1~2I&g-av>K?=jVtTjd)RMhL?aSVdAS8Ac}4XTa8AgXI9x'
    'g#7vbt9j?9DwKSX<_wpx7-9jzshwJz`n*DV~L`+Y?bPfu!W{5eiM&cf5~T#BTh90-=M#5ms)Pr7Tqu_8?mofCg>H*;F_vSEqkGS+`krkEf7DrEHN'
    ')PnW3+8;OCEY{6M@tb54w7VH2f_s$i>>WNEH$0n$n|eu5v97&gqOKR*jIIzZ;PMrcOi7FKrtwNm4rQ)cr^W>X#PsV*H!yODg3TD-bPFrMVQg2K(3'
    'Oumsg#?{zMVWWoPFj%^15+jvdr|?w#<2ID8jzl;qwQ!Nj40mnFC<Wo^Zo2xsIrD#<DQxp}hU=)ms0+tcRQv6&WQjN21&98l90yY9ztPKmpimaZp~'
    '8r%m80s+CZ}Ql?__kX1wJsC;GV?u|D7dhW<6Cpx4$lx&1uOj~roX@-)By5h<}b+&+zu07L8gcU_4*O%gUpaPMc$v>xXx<yU&Vwyc!8}%2*?}T7Ib'
    '3+>>P=FT-#4mt{8dWEgX`YOcnud7g=Cx%6i~^gs_hgM}GzgFv6&vvsd!!Ouo7zT%;{@Y?3DaNZ011a%?QmnafEBBD6g|BZKxh^E0of0{6H?l^TR>'
    'q03jR>h2o$S)d3gYgkD_bB=^Vrc`0Af>iKybkf+ezvZ3_T6dXT7?CHh}-9kr238N%gSf>~6&YZoSxQbi{_nm@xaKumsIog|D7?j|t!OHG_i5H-X*'
    '-V!EThFH72n!X7kma+Kle}jK9VsMeAENPiWCkBwrvuM)ASne|Md%c;4c#Mt=38jYt%%`K7TDWV^h)Ccj9erVQk)|AN#@fjbN21G#xOa7I9NicJB8'
    '<2AFs%92y+B5_H&sL!-Bv9B+ZW=pquD&y91pNuQNbl352pNXwdfj@#KpY>?BjKAD(l#~!*U|*gP?mVU#!AKNOX9_2=2+QYv#d|SckO}@UA{$5*%('
    'htWVNDG=q+t=0gj|-6=o5<tA-GaFF5IOt4*ZI>1~}0E$!{^<K9lj-f>HET1A(OG@!z2+3Fb>}i5N0!|7vcOmj*-1@?)<qC&0<j<OCPaEjST$aUj^'
    '&F$YJvQ)0K;%#t0cmvf76-Bop=}zxW}A_94CrbK%9S!b-~z`B`)qr5{DQ9g!k&CJ?JhT-AQ@Ujohf2zcPgJ$xP0VugDwepXHXI*(b7Ga*{ssBzdf'
    'xXGnh4F)GE}&KD+UPfm0gV9>T9y`4hMbhZZy?S!Y#e+%0IFVke(theZ&`)?9U1TR_X{7~b57y;LHK`19Z-#c0e7x%SQEcgBv5%?I&oJa3e`%(`4z'
    'aR9;0q48Oega#WKML(__upXp&o*OjySR}T}0FMB!J~C9^fPj~cGD$N2pnj=7u8PRewjV+38Wl7ZJL+(G1_SQAb?soRed^mwg0JuIZX1MW+~x60gV'
    '7f9vX3sVyR}O>oVK<}8kPqucTOMZ5Hg9G)WHs2Akz)n)@GA=>L3tBNN9t_@k{jx`b%kYO#lbfFLa*|k3(LZgjOqCyc*Y*n@ZX#*LQ>MCdWZiac2K'
    '^ze7|85|`f-LAaBE9q7ixQ`h5ZfgeWlcOr03Cq4@x-99Z=cM^`40FMli9xBSchN3a}Q5Dw>4g(zBEE!&FcAzVpk}*N#K~wb$N7nSvnlrq>BgwO^p'
    'z^zRLpi^nXU4%sl^g&wlI`sR^tDq$=pi?1$D^~MKnr3JP^ZxeAAKY8iVamJ+lp|E5x!8GjVmf{G0_W6zSB^)f#=~WWSNA8;W}wq23xnSNhgj@qz0'
    '#W%B;0-`6Q$Wh)!ixtxtY(?-N3mtx5#7Rop<2KCpwp37$(E)eCt=U`Y2-;ouSE95m(yJ#Ku-cZ;>HuSPV-#VeYzV`#P*K#%qPXv<S5xigwhC;cOx'
    'W?4F|ZWa0Fh;nUx8pG_Q8a_KpCMvZJ`+sK@gl3HR+eW_Ksd)nfOObq*yaVNB^e_Byml^NM&ZE!7wYXa$eM4#ea(cV&=W6}U=Wpra08Een@#*Q?ai'
    'RwBkR((6hc7lrqLKR6uV(+p3^1x(wX_1-y);n*&Du&}qHk9&nqWPfSet<{6a|q{8FPq4v@|5w1SO&UlwKe)F+T=y8ibv|9Rby7h=M1CIk+KSIz;5'
    'R)5<d+C2#8oM8_yvzC`~0K#4j#$U7au&<1@yH`V)U!TC1L8I}?X;SsrLGx)%O#-zt$gGdB47}=Kjz<Vz?38M$6nm;Zwz^cN>D&)Ct6h|NY^4=zm6'
    'YeS2qi4!`L^DX+Yy*Nt3bE5^T!Gf3D=YRAbSv<@ym5HW=*w*leYCB?8i{buFz$=%w@z&Dxd#5z)4Yxc=s44wyk%`ts&%|wO;n0ShH&u+gB<vXv$>'
    '|rxieOisyj^h#A%5&0%TOgRxWTwC{mKO8hT!FTK&B4Wfbz7$Vh5OSV--niScqJ8Xeims%I+vEL}r#Zkvcw8r3s#I$#CLbullegCilV6+HHT$Mfv='
    '^+~#n=aOF|-tu+qJ^;dxEWzYwGgsn~0Jtuq+`^b#A2lAT*`-zr(A`BJ>@y!FFmUn8^#xG(j<l0%?$_~7=$DuF^%mM&oyrh8`oS7dnavu<z3_4+x^'
    'Hrz*E<ReriqZ9!pJ%e8M3lM6nG%8CZY{47Mjb0PSpP9;Go=loqKzyq2bw0N7a(i%WlBicE0i&?}!DMBc%-wnM+y%D=!mks}X4EP|Zp(=5DT;tnuW'
    '~xvrv-(de2a`Su*A*--tnw63a+Fb`%t^e_cs2w?11iqtJp`@s<?9fL8O#8rQ*Nkf)3jpr7K>I7P-4+=(n4L~AK#FK8pBjdb^Wkn!G`OQurHxXzl%'
    'SDd?%i{P(7{MA#i!cJ?4sZ{2O+d9TM3Wg#{87}FPm!y*#>O<pnM?MbT530HO0ETT4faKj;gzy`c{-;Ax!hYF5{tI-<DzuB{8AS0ymce;xl!;J)2$'
    'W$Vl=xT_bR`ytun_yXgJknk%qu?5h)(t;l8hKw@55%Hhn~Ml0dpnI~!v|#jVabsd?F;?&ZWFg-ierJICqs9j%5b(AQu_lI~Hq0;t0tKrEg1YK#DP'
    'M9IL}cA=bZO6kfVEB4@y{MWGNKCxDsI!b+PD_;g#cj+=5X?3S0$!&lVC|Q5D*aWa8-kW8Be6sUWvL3jGeL1IAA!9-2Ll63Rhw8g3o6kbuwnZ`kda'
    'G#Qs)LKnH1OmnYak=^d0|0IOOLGR8sn5K&3xXkk8!0@m``Jh=@n1UKthvpkHt*3soux#q4!Ft$95q-OM8|4$)~pC-i*a^%+7J^$tahd3;Xv_wL-='
    'mypQy}-_=Q!r4t#uw#+8eo(eHI<4Bku+FipolB0Z3QAMF_jCk}?h$@m`?1E3yGqey=Mc5l*NyI~&C)>*Fc{-N+w5w^IWU~Xn&wztwbR#Cl;b>TcA'
    ')`Dn&m^!KqFU=pV&VLaAM+$hm|+--S+1tctv|9|!J>(nwWqQl(&52VAXkT~$kiy`qC`xcD>>+xR%1D4?cgZvGfxN^O+@5&qU!A+DRlG>JlW44^~L'
    '7M*dMJap~Hg&7C^j@xyI+w?kVes3Zynf#)k!EZ=04t8K?rIn3&2if$azNYG|XE1(n`TRUXPU9a(7uXJ-`4eY0OWNbWh}(BGdMs@+@4>KCO>-=lXf'
    '=qh8$cgA2sChuct!t!2VF6>$<!m&?^mBBePvS3P6oJqpvVwsf$vnLD7Qv9(c57T3xjpwlN_TtB<szzZZ7w>VBD%#?9mnJ)1T97x6BnpcXoCa7AIi'
    'OJE?a(6ueierMqz1Os18UPoYv7WyZDhzMEk>%{L6eREt}@a^a+C4=nOU(tI~Y9w_fQfVIm8U;M$^mHsrMvcUGjv7sX5K<;_*}ItXlOqy&okxV*1k'
    'IrJ*8%Dy_CbnoQ}5TxI!#t?dA)FX?zO9>s#>^?dkfp8>kT)|!j1amE~JME?++EDZskTeG%FDS_aw8Fhuk(mF0%|8ftXhXs{1k?A+&VakjRQ)mOME'
    'GbFCi92ib>{`%@cox9*o7SatBDV+Mk11L~cvC1rJVvF?yKGbT_*BV@=w)3@mMb~wIZ>*{`NX)55t6EtX~1dY{kBLl1H+Jwx;ynSiVvJ7{z`-d%Jq'
    'x=Ip4SSt_Ic<#N%>IHin0MJyGybE+LG7NFH6a0~V3e4mSC=p~*ZlGkvv>L?O0K6{ZBQIF=IYL!s;*#uOtvPYRK`ysrE8a%EFYJa@0^XExXOwTO+C'
    '!PH_9#1#*?H@)pb)B&gl)R>yxAeNIR@fu^b_j!p0%^Oq!LQ5{(BP^wketoa9zC*k=PnrcVXA&3m0hNpZIi_@romXH(KnH{CDnP4963Z=W>sF+EzS'
    'Ry0Spk^WGST8}CFm}mzSZ2xy<f>yQ2EDl1`Z@ca})LAQW0;+g9LK?EPF?Lc7yk~@P`sgl5qaDFy)ftA}WE<P1%)N1F)+^W}Y2bl9fOPTYo!e4d94'
    'h@xX!)ZnA6=|M&}@pML)M{Df30NEar3Rj$hw6Q<fpdu_!&k^8#7?fB!5m}P+yItd^@Q9L1_OHhP4qZ=LVm|Lcc3Qja{-xMwZk76;OJGfQGmFih29'
    'Vt#@xGEFFu;c@_;qLOvT5dir<?pkW7f#EpYX8%E1KDz=0p%_ciA>)PjoRrLEWGG>E18fwZ-A#NjQY`avM-H{uTgG&syETXZhwW*Pn3|;F1io3{$T'
    'LEyd?R0hN-;Z`+MpMHQ_do-}?HvU!P1kATBuwbc7~2$oSa45F>RZ0)<wZBmNTD7Z5i{rGH2|VC&kI?xm3%2{-dN;sPc<Fub!?TTxzO?v<e@p$>Qq'
    '#Z-GdqZ)Diyi;}5o#l#CcCKdmyCKSzMOVN(sR|k1u!7dEX?|T(t6{_yh5HaJ5G@hcgp9pKKx_u1fElwJQ{gg)VO|!JKLMO?vm@1AODaqWvE@BRX('
    'NPg=zF5wKqe>-s8$wkvrMVKX(u3EK^e}}AYysCIQsLC8484&xwAdt_j11n(~g;p8BWajGG0wfwuz#XG@8Bf7`WaSMb%^at`V1`)Uix0#ZvK5vV<b'
    'sSgX!WC4OTS?1VzfbX!!LRa=NU$P!6|!qO5#Bk62kSB4vw0U1{bgqmH=jwUFc7}Ui_131WI>;z(aKfBNsxe$l>UD(xZU4quZ{+ZuN1coacWA$FE7'
    'R&kQ>_s6RyzUG|U=o6rg{momowVHsq^z^2)G_``QSKOoY41O>uLR2cRzmj}7<5s&L!$LN9Y()D>DG2Q2)g0+8wK7zj1PRZhYFVwRPxFDf)`?BYBS'
    'ZuxpF>}JYRrWNNe~}cpz`QHeC`WH<C9pvisA>j9##Ic$(ds^<rCsunc~``UufbM#RZ%F=$}3>Md?r#~I0rWXXMvk>o5(%zi-O4K80K7@f|rRRS0j'
    '3YCG6$D*LGRmcv9t6<Yo5Ms-876hm5*sWSthtCBD-&jFE%Z?@csa=xXRn(!5))2Cx5Md*p>3w(f1&uq}#{I}xJUG;W4b?_m@Q$s;CX1oB$sdd-Z4'
    '((1^gE|KNT%Km@ZXY~g-raKC~f5tL|f8etNIiesmORRcn2Mnovol&YM+arWUVpc-WO(WX*9(}bYhYer1T-dN?iaRF;AiK1(k+1koN^Fw!!F(W{;Q'
    'Yo4Ke|*4uQxR6fw8Y!XwUTpf5@4M;h;wX{p0%PiX%UxXP-a*n(~WR3P-R($vCE{%J1Vbco%oi8ZdOu2(+%eTLq5HkasVm)V2z0$Ru>+YqEO4&mF%'
    'PSW<=@Qb^>;3dCbxut1uHiC*Z*3hiQsM)Wdq)OX(Z;djwrec5V8Xq!6ou+)T(7xst5^YbONF2((!?~d3M`bglS%Umz_1eT6Yec!ZDI1DthAY{ZDZ'
    '4%u-&7F`MO2@^um_5-AlWe*<mi0)LBu&l9A?|_Tkc#sU(|m$d8Jjxa2Lc)7iEvw8qmJX3q6?bpu$N==5GIp}eIYOgxBSTgeh(x#WYKnM4^BV2kyl'
    'ml7V%xf6*AFZSo9+)lUaMvcjoiBH^nL>bNtciY+u)B|>^38HA?%joM&P=o57g2bMC?MOJMD>Vij;9A-lE0v{BL3mE}-~|l|uXguHil>_mJr<p`wA'
    '|-RD{xEy0FDrp_a)PPsj_vQ^gZ`isR-ZE?6L*Y>aE=_5azlU>lbKoP+SCXrP41@hadL<w%B7~*$x1KRXOc-rE0VP?j5k=MgyosB!~e^<rdO8?>m#'
    'dNK$JOe{5hIP@`_u5oaL<Ry4^kTNp73vVB=voUJ4EkxYdXLZxXP6;mZlv*%LIs!?7`kdu|m+k{|P`GP{Zo5SPW-IW=E(2tVt!CjDS&dTB`YmOU4+'
    ')!1u%8UrHCw#6M#K2@IC3}eqF1N`YnIf3Y8qrd~hBZ9qd`AelG1cM*JzrDhw9sMF5tS~KPSDhYzmSdv&>~8C&51AVoapzk%!NERR2lE6QHD}Or3x'
    'vqU9Ha1@vP{N>M}=>)B~Y36UDD-9d<5z+BwrkNulT>PnmZlE-C40GsB1ts7e^5uB1dMG8)jqkPnGWy+HMu25($LZ2Dm%u-zqy>Z~@K^<|?LKaVZs'
    'wC+IB(gMC!48uty;H(q?oM^X3dotiv5#Tnf0f|ULnxro_L}a%`tsMc~H>y{USBu?M)SH7Gfu!UBG+vJzLv?piUu;nd6Dv~b9VamdCAjfj5h7k5R|'
    'o*O<Py)?MC~)baPV-3htlU7s_|9TUk2A;@0gWEGzUH?hdT`Bd?l_pbZ5wkfvX)ZnIolNvWO9eCwg53lmvS&rV;Nd;6>A?)cYdttS`h|DM3r5=MWR'
    '%ei%obF~}`QX`Se%YwT_2F~-14*y3ZRkVx6(NVQSMQ(9wmHRXWx3}a$s|8j~Ed5u%o!Rfigd>>k6YiQW9BH6T#Kd+o{e7X7NukBl5Vyy1y>>Nr6g'
    '!bOGiU3PwlBIaZB$PN1P@tma;Z;p2f}W!|4<c=zx0F4knoFqS;~=7^&v{RsCF{A2>W`#6FeBrLo-?VKb#qe)gHBN7TykNNPUEMnZ|2-ZG_amp7A|'
    '^L`1<vw?s(_Hwp6evPPL;&l~rmx=8p7kUo&@(TsU#wt$Wk%YeX5cPRW$e?ip6a#*<juPD4bbSSpd(%Kax(G<P1Y)=NgH2XK#Ge-s&F9_nt+h~Dul'
    '@FHKN^XZ_YDrQ`R;+F;GR@rH9Ms{fbb{J>xczqQ_3B*^f8<mpKp)br*wo<dtnY14jdjWVL#Y{G3Amwy4C`z-oBtDIWsT(u)d}GBKCeP17t}ad0L)'
    'Rc`?UY;kiVj}F=_f)uS&Zq6Njn|0vZx){?>ui_WBwn_qHh8^$lZdeNO&5-p)i6=&}U*f;FM2sel?2#q>Z4bKpR=VAkJWEf}5OQ>Ya+t;0x4kctt7'
    'WC{RUEH~N!&hRpZ>KCia}Y3K%}WfLmQLxMow{42&m>m*ll?7B=S?L(JZ+F3kSg!7J0n_$S4O`CPwZ95#YNULT{LeRphF_P5F*=+^##`dMKCMl?u%'
    'WGQX2O_msFFoS5v?oUy(XIjXG({Rc3>e)DYh?A_1g?;*^mGJdICrX}f<*L)fjv3Uda67)fvr>-LXXM3Y{S#;ml|@ov4MtV?&2}=fK=*@NUc@`s%U'
    'RWt7%u-ObNe#<Ibxp0`_1d%g`;@XnW&Ol=?qaR3_=&x=^~T^Es8qj=@3~w2GQw#Do~&w}7Y-R)e*z!r_@hrOh-G-Dd5|gk`0O>rOz7p5*wF%0%Ae'
    'k4p|2w5MDYYE8CAr6ne5T*3rPNw+&yE@B`6Ay$JCEfobZ`-wM?@q)Zim4HIs9dFu~Qx^+otIJz!$E1>`vM4PJIX*;s@-=x>2d)!Q4!6Whc$2igD2'
    'v&Oaq&mWoVY?UoZGd-i+h*VwAj2dR=WbHjsRhdi`1OjJ{a9QX(XA#>KK9XYJb9O^7%II(t*RA%Qz_Lrht9Uea&*VhxOq|UExSZ7WYzmmENbY*rV0'
    '?jTc4fX`#f#HgxPr<K~jFJPUXtvA3FU<|aK2d2tsn1M@#ygs@d7L4I+9eM%@Wj%iGk=~*udQvg@)Q_1V|TORc7t?>k>D!Nd($4Qp2B!fN__M2bL%'
    '=;Tyct%n}dMxpxUB8M|wDGcMrYZ}bGbm9vO3B5(I+LZ^$y<|)P{!vBa@yJq8m-7>emmZTcCp%Zs(r-Vr~NmXlIwtc1%#H4x{p!FDau=gAe1E8k}9'
    'g);*Z{x)(i^}q7o#?qntAfi(QF)oNNBz&33Ah0h@K>G%Y(47US?*7~OZR<E(b~vv_H}p<Yh<A(lmL*B7a;3F@d9Zdwjnk`LlfT+q~HMWdWYSBe!M'
    'q;eFU40>%+cb1fdkZ-tKOXX>+yuR=RKJMXEd6o)Zb%}raj^H5jceV-a09b+Pv#P7PGFcU!8R<n(rFkJ;R*}mu7P-W^oOZ_A<oiMwS(I1~SxqA3mz'
    '=C3gSp#0Wor8rX5gh3#Kx6=|MHE<Bz>ZM1*>pkcvZ=i=;B$s2>_?RxX|WSM>RZp;-R}@7=y65L?m(C$X!K+iSUD%YCY^mobf~)42f&&sGUz`&T}f'
    '3rnMN%p?WL5qAC_rxpNxJoEm@$2q%CmH;Ukt+sBlMK@r<Z1Z!v&7^m}+IZb`%i<(!H8opWLVgnN_S3$+3D^qC6XAq;p8pbe)w%C7gz2Oyh0IjcNU'
    'hZ+lf&RRVRm1O#vEokN3Nt?SfZ0f*6e$U{xKMeMai2J0B_nPnm*L5K*8cM<zEn94&7~%74cgHOsWsC>(Zcr5@Q&`Fmt!?1*g=4x$xFi}VV1ZSn&&'
    'aWR!U5=`i7O1w0kp6;&){6qy~jD5&LKh09RmcLOi?(7aPLO^~MxAeT<-2fSe6T?#tBhPe-#mN2S>rrQ#!Dr%EMRBfvrRyQGpVFKu<u`tMyD*ZreQ'
    '>;y@E*2kuNC7L){n|%M0y>&Z_!2gb?`TDK`JJc^olh;<g#W4u=Y+QsL^46i6@s8P|Yk9Y2O(Qf)0jPfbJP4>om$%1{WGIp#(fW+`-RC8IS)BsoH>'
    'U8-siyhf(%KGpg>?6AjGWE(?he_6glVv{%OeZA^^XnB)xi4al0}Bk;q?&IYaCr9Zr^EBP=)=Y{!;Pm^p%QSD5ENbCvvWQ7JSB#iS}@zrB95V;`AA'
    'In{)+OVB-Np4~p<86ilw?|N5`!>@36y4L;)o)1d;=QJ0qv01oPzIu&r$5%`qozJTf~WBF~<MJoNNq6r6Cs#;@?0;{<Va_-e8M@MTYQBC@5e;?SWa'
    ';XX>uRbHRQ5`QA14;2D&H~!JR20-vT_Jdo@YJ~^npIl@D;5hK?U>|6rT|8iY*b?ks=>B^P|O|!uMsuY!(9wN3*(qpgb51H=H)1^h@%0dG?ddd=U-'
    '|NLblzQf_ExL&C^plx(#797o}l(eMB9bc`v-d6mcnmr<SU+g<TSxiWg(>%0@t0=}b1Pw3T2W<RO`J+w=OVuTRglOdH&&rY&vHN@=sttd3vI$JE(j'
    'mIcacRmjFLzQi>Rt(tLm&LG_neg;zZ-h@ieF;Zmm6OH28W*>CNHzsl3O(FwMtoJ%&e3w3-oa@WyBu52zBZgA_o^j<}K$a=^b;V#<20J7Tm)?mBo1'
    'v;^J*qYd?{}Z*w*~a32T%T`{CdB*vti9nC4|9Hj>j9g(Vf!5E8{{`Rcj}<4Xu7>-(tGfVTWAh#e4??bp)83t(G2BGfU50)sC52!HS4_YVjOhmUg='
    's&!fC8p02|8cV3top8{ZfHl@w6g^ZoWGG4?af{iqPseuz}fwx_%5LdBbg)TD9|MQi7DjctFYgDK?$eohb3Yc*tL#)dI2+^}K(a#qEXA7&1bOeO(9'
    'kB2MnmjG2oboG?C|iy4))@R|)b-}A&jquL>-yO3nk;}Jgi9^*ewx`j>u6k$5+zUBy`g2X3mdC{Xdsu<V^E?!sn88Mp`8oQAQq*Fx)c@ybG3Yv+nw'
    'fkscPUO+L7e&_ggv>tCIPJaV~%<1jf3B@&9B;2v;g5FXa|Mm6mhAh+))jxAH2`4qP8XE|vZ-3D$MPB$a<Jz0_H6+mwh5_K9Yl$GrHc$a59jFKT3g'
    'd%e}H&K&c~go3h=fD?=l2=%4G2Uv>aeYiVomu$5KWf>dQ9tbOHv+`xl!LaiV<g$*w8bbw;6w&B?apT#j<hmphffTC<2a@g|1~tyY^sT|n9usoJ)i'
    'c601S;ag7&4|sT~L{o&jrv~<sl>yElx0CZW}doaw{r;flHE4B2`+x>g5Qi#wN9vh>tecJ<{I9ZiOEg?9bk|J}vnIC}$kusWIY&Ty34%?|lp{TsjH'
    '^8}e}RZ^Dx1c4~nuoz~R$&K_U?zed!WLutj28{=MwMKris?c!RtfXR`ujegN+WlE|g1>X&aXOE>eNx>Upi~w4;NC1cW7NG>O;QJ3heap}Q6E4KdX'
    'eYO&V+MW^tBON6=P>*UUcWB&x$bH$n+nqB($e@bk85RRq`*VMoYkQa8N3oJbKr+mR>q-smpbtIVl9a%bktDrScwJNryz5)xK%-D73GT!awjXLH0Z'
    '2|{u-ckGjCH<6D;TM>QZS9pg$|iC3bcZh>F6J)v3~dkp2V3hE-xht{L4w=!Q^sh&a2c0(>c(z~_xAtWeeaq7$7Vtye|gTBJiOSpA|m5j^R;xTgU?'
    'b~9vBpEm{rX#b}{9TOwBsiq>ZYU=;nz;)M*mfM$>;8e8Hfo2y=LBwNZu{EwTI#O6CW`q@RLzMEVz-F^h8}$e1oPncjw+<D>pks`%(sF^@K97i|Ix'
    '19z`A^K?r5)<Xj%8&^sKaD(kJlPtZ+edNB_@tn7YiPtD&D1a$MgDK?-IkWOs)CUgy~C<9w3Wa%Wegk5+gXiXjj|ag%Nw7|8Z@w`OvpYDt^;a6M9G'
    'OuxKy<l0(sl9PrtBSkbI1G_*8fcmE@}<kuV~+lF&=`QSb~oM90!GE3u0%L)#+nrqfhYjgA|l#(lJ)5g_Gm~NIy37Zh`k6)gC$$j1)y|t!{1cNx>?'
    'NEIoCiK}X{|2~jp^OixF*O#STxRj+*BFlO(e3spS}M9?XH}#F%nsE~9#xb~dk4V0R%_S0^RGyLAgG??-Gz{DI87>6sv{rn^7cXrgs1e)ic=Ut9`0'
    'C*G#r3CS?aji;V<xl(M=J)Kr+gVIUq5<tW^;;A`>NC5r&WFR~DOWn&1n`hJ@BB;;(@0Y_(>}c0;AM=H3Fyh1_qma;Iaz!F~=(U7CjOb)mF{UVTKY'
    'rO_vdo4o2CzaYUA5qG1U3=Uw8x=Ov3lKc{H*Tes6?Y(?N<r-=UgSy1wSVR|_6QVx=WAUhypw#W)oiowu8Tp<IEWfkCkKPCS@4#r|BE~0*5#^i+iF'
    '2fVyp*{9`4Wtbux@KT_@EJ7=mO9AoJHxZ$-{O`<Eo(YySCe$Idx^tiecuB7<id`z>f#?udXXjOUEf>SqtS|go$oe+7r`e;(|gU5f`P?BnV;WuDI*'
    '{{Pgq3=ciJU`o1mWG@xRJAZvrlj-83L59-yPrk3hZY?M?;)%E^mvGrps*|~GK2#(EQt9v%?Buu@CA6}2e2H#{5tTfcc(had!)6uP$Ju9PYp+35dc'
    '^=okOt0~fi{Zva{DK(0D~4ZJ#2m?vaoXyb{tv4*lMFRN<z#I?3N?>oj!f+Ty=o}sG`VX)ch^n$igNsE%ewjl2(+BnB7!JF(UfwHJ$j}0MR%Sj+kv'
    '~mTAo^^8kcm$x{)vfc6g#X#RYZg{L?Akt`Q{Ht*Ow<q~HYJd`X+$+YN8zY4WC`lAcGH7<|L6DwNv1rj%|ZWRfN`s`L)0d#|J1v0+7fO^Z+p1*DaM'
    '<C@6M3ZPRC90xi9l;L7Xe7bz#A=>CSwwt<L*C;8p&JGh&3Y|_oyLJtC3dcc^w$;%#khEBW#tz0KS~j$n(6mKX-GK(wlic<We`A5M#kD3`;{}kzJX'
    'O0|KV~VNF6E!1iAAsVJD3wG9T4gdvSMRYrCcdY1S8*d5Wg|>$5C~p+0Rv<HnZHLmQ{#JG7x1AAx{)N)!Wuacrq#p0xqtfe_U})Y`81i)JO!hB@7|'
    '(Q<0Ud^ra8JUYd4}7|go2Dp&h8JQM5AH~_rKI950yX$zb;B&Yh^$KlWy5v%I^4<K_f!4Z)kmxL9ZBz>Kn;RK$@yiGvbv2)&KKC3NB!fV^o`P-N+Q'
    'yx+0-EP02$URyr@}FUL;Wrq<^?PKmdX&xD&dZ%2Q>Rn(U>=TUhvayAbhGu3P3>;4t900ZcLM9l(yBNXLKH{WZWJrhV)UGbx>HbT%Bb0OB~cbG=;n'
    'zf=5Pbu<b7XREr#v7ePUBru;$}%F2Ip6229BeGI>KnYXA7sTH^`5N%~O2Z;=x4o6Q0;F4&G@i1b+`08I&Fyn+{cBp~xZJeQK&cAnk!;icf1s~wRl'
    '#3|fe^~2hw>HJ-BE9;$NZP*9SxXqsgMtKlYi*<M1TD|Y=*c}itFb%EOpujJ*h|`{;m^Qxo`GtU7NX~w6Jm+qkDd$I;?sjF&05~SLrWNmy;Z{Hlp='
    'fqk4x8L3XoO3FFAu2i(fl?Rd8p*TVYSJ)1FPf@`^R7ww}&DfW}EG@9l{9@hg!TZj8h3Ycbw2sX=Q<gu{#K}lYPlBEt%e44`?;p4e*fl9wueR@jt-'
    'o5AoUXA8Xr=0!h|>^WE6Q?WoJd>>Rq#2a&aw6WO`<VYpHHaNDgXvCV~bxP9c6su$4x@ljlX6OP)(0_3(m+Fz0MXjb~7S(kXLd}}5{%XqPfj0W?uo'
    'zo+zfEv*#5OuQh_1DR3EL$_Z7C013k;&nT?LtSN?FOZKwi_S<u{vlvH4mjp&e}irRnToWJ*DTVjn`-YcnDT*g^t*MV)1VkKdX$gewgIG&c<=K&)9'
    '-*)<VJrx7moMJ>@$F0v4X%;m;(>9WK9pyw5U7y*~gzu3H~=LeBI81s~!hu2$(qy-Vu{9yh5sw9~2G$l9Pi8ph>%6H>$L*jEV|E~2U|!7+RxC?4*z'
    'N!Y9&v+3DycZT_lw~FG?&vq5uxxp6?POSGU6op$IVx*Lx#;Mlq%^Lt&v&)Lkt@Vm^$Rcctu7|&DD1b+A2kt5p#t*!lWKnogHONnNt5sAg*#KL;$>'
    'P7)ZwU9<Zq>)Y2oW6iZ}`B={{d2n_f`'
)))


def _scheduled(observation, tick):
    seat = int(observation['player'])
    count = len(observation['farms'][seat]['hands'])
    scheduled = _PLAN[max(0, min(718, tick))]
    hands = [list(op) for op in scheduled.get('hands', [])[:count]]
    if len(hands) < count:
        hands.extend([['PASS'] for _ in range(count - len(hands))])
    return {'farmer': list(scheduled.get('farmer', ['PASS'])),
            'hands': hands,
            'market': [list(op) for op in scheduled.get('market', []) if op][:10]}


def _post_action_shed(observation, action, capacity):
    farm = observation['farms'][int(observation['player'])]
    private = observation['private']
    shed = dict(private['shed'])
    positions = [farm['farmer']] + list(farm['hands'])
    instructions = [action['farmer']] + action['hands']
    half = len(farm['tiles']) // 2
    central = (half - 1, half)
    for index, (position, instruction) in enumerate(zip(positions, instructions)):
        x, y = position
        if x not in central or y not in central or not instruction:
            continue
        operation = instruction[0]
        inventory = private['inventories'][index] if index < len(private['inventories']) else {}
        if operation == 'PICKUP' and len(instruction) >= 2:
            item = instruction[1]
            requested = int(instruction[2]) if len(instruction) >= 3 else 1
            taken = min(max(0, requested), max(0, shed.get(item, 0)))
            shed[item] = shed.get(item, 0) - taken
        elif operation == 'DROP':
            for item, quantity in inventory.items():
                transferred = min(max(0, quantity), max(0, capacity - sum(shed.values())))
                if transferred:
                    shed[item] = shed.get(item, 0) + transferred
        elif operation == 'PLACE' and len(instruction) >= 2:
            item = instruction[1]
            tile = farm['tiles'][y][x]
            if (item in _ANIMAL_STRUCTURE and isinstance(tile, dict)
                    and tile.get('kind') == _ANIMAL_STRUCTURE[item]
                    and 'animal' not in tile):
                continue
            requested = int(instruction[2]) if len(instruction) >= 3 else 1
            transferred = min(max(0, requested), max(0, inventory.get(item, 0)),
                              max(0, capacity - sum(shed.values())))
            if transferred:
                shed[item] = shed.get(item, 0) + transferred
    return shed


def _baseline_agent(observation, configuration=None):
    """Kaggle entry point, intentionally the final callable in this file."""
    configuration = configuration or {}
    tick = int(observation.get('step', observation.get('day', 0) * 24
                               + observation.get('hour', 0)))
    action = _scheduled(observation, tick)
    if not 706 <= tick <= 718:
        return action
    if (int(configuration.get('episodeSteps', 720)) != 720
            or int(configuration.get('turnsPerDay', 24)) != 24
            or len(observation['farms'][int(observation['player'])]['tiles']) != 10):
        return action
    balance = _post_action_shed(observation, action,
                                int(configuration.get('shedCapacity', 100)))
    action['market'] = [['SELL', item, int(balance[item])]
                        for item in _PRODUCTS if balance.get(item, 0) > 0][:10]
    return action


# Apache-2.0 own-action projection primitives.
CROPS = {
    "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}

ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP",    "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}

FARMER_MOVES = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST":  (1, 0),
    "WEST":  (-1, 0),
}

def _shed_access_tiles(board_size):
    """Four inner-corner tiles around the shed, in NWSE order."""
    half = board_size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]

def _is_shed_adjacent(pos, board_size):
    return tuple(pos) in {(x, y) for (x, y) in _shed_access_tiles(board_size)}

def _new_plant(crop, day, turns_per_day):
    cd = CROPS[crop]
    return {
        "kind": "PLANT",
        "crop": crop,
        "planted_day": day,
        "watered_today": False,
        "consecutive_unwatered": 1,  # planting day counts as unwatered
        "yield_units": 0 if cd["ongoing"] else 1,
        "max_lifespan_step": (-1 if cd["ongoing"] else (day + cd["max_yield_day"] + 1) * turns_per_day),
        "fertilized_until_day": -1,
    }

def _new_animal(animal, day):
    a = ANIMALS[animal]
    return {
        "kind": a["structure"],
        "animal": animal,
        "placed_day": day,
        "yield_units": 0,
        "consecutive_unfed": 0,
        "fed_today": False,
        "cared_today": False,
        "fertilizer_available": False,
        "pending_care_bonus": 0,
    }

def _farmer_position(farm, idx):
    """idx 0 = main farmer, 1+ = hand index."""
    if idx == 0:
        return farm["farmer"]
    return farm["hands"][idx - 1] if idx - 1 < len(farm["hands"]) else None

def _set_farmer_position(farm, idx, pos):
    if idx == 0:
        farm["farmer"] = list(pos)
    else:
        farm["hands"][idx - 1] = list(pos)

def _farmer_inventory(private, idx):
    """Inventories list is [main_farmer, *hands]; grow it if idx is past the end."""
    while len(private["inventories"]) <= idx:
        private["inventories"].append({})
    return private["inventories"][idx]

def _inv_add(inv, item, n=1):
    inv[item] = inv.get(item, 0) + n

def _inv_take(inv, item, n=1):
    if inv.get(item, 0) < n:
        return False
    inv[item] -= n
    if inv[item] == 0:
        del inv[item]
    return True

def _apply_unit_action(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity=100):
    """Process one farmer/hand's action. Invalid / illegal actions are silent no-ops."""
    if not isinstance(action, list) or not action:
        return
    op = action[0]
    pos = _farmer_position(farm, idx)
    if pos is None:
        return
    fx, fy = pos[0], pos[1]
    inv = _farmer_inventory(private, idx)

    if op in FARMER_MOVES:
        dx, dy = FARMER_MOVES[op]
        nx, ny = fx + dx, fy + dy
        if not (0 <= nx < board_size and 0 <= ny < board_size):
            return
        # Movement onto LOCKED tiles is allowed: a hand can spawn on a locked
        # shed-access tile, and blocking movement would strand it there forever.
        # Tile operations (PLANT, WATER, etc.) still no-op on LOCKED tiles.
        _set_farmer_position(farm, idx, (nx, ny))
        return

    if op == "PASS":
        return

    tile = farm["tiles"][fy][fx]

    # Shed operations resolve before the LOCKED guard. They use the tile only as
    # a standing position -- the shed itself is always owned -- and three of the
    # four shed-access tiles start LOCKED, so guarding them first would make the
    # shed unreachable from those tiles.
    if op == "DROP":
        if not _is_shed_adjacent((fx, fy), board_size):
            return
        shed = private["shed"]
        for item, n in list(inv.items()):
            if n <= 0:
                del inv[item]
                continue
            room = max(0, shed_capacity - sum(shed.values()))
            take = min(n, room)
            if take > 0:
                shed[item] = shed.get(item, 0) + take
            del inv[item]
        return

    if op == "PICKUP":
        if not _is_shed_adjacent((fx, fy), board_size):
            return
        if len(action) < 2:
            return
        item = action[1]
        n = int(action[2]) if len(action) >= 3 else 1
        if n <= 0:
            return
        # Seeds live in private["seeds"] and are consumed directly by PLANT;
        # they never pass through farmer inventory or the shed.
        available = private["shed"].get(item, 0)
        n = min(n, available)
        if n <= 0:
            return
        private["shed"][item] -= n
        _inv_add(inv, item, n)
        return

    if op == "PLACE":
        if len(action) < 2:
            return
        item = action[1]
        # Animal placement: standing on a matching unoccupied structure. A LOCKED
        # tile is the string "LOCKED", never a dict, so this branch cannot match
        # there and PLACE falls through to the shed path below.
        if (
            item in ANIMALS
            and isinstance(tile, dict)
            and tile.get("kind") == ANIMALS[item]["structure"]
            and "animal" not in tile
        ):
            if _inv_take(inv, item, 1):
                farm["tiles"][fy][fx] = _new_animal(item, day)
            return
        # Shed drop: orthogonally adjacent to the shed; obeys shedCapacity.
        if _is_shed_adjacent((fx, fy), board_size):
            n = int(action[2]) if len(action) >= 3 else 1
            if n <= 0:
                return
            n = min(n, inv.get(item, 0))
            if n <= 0:
                return
            current = sum(private["shed"].values())
            room = max(0, shed_capacity - current)
            n = min(n, room)
            if n <= 0:
                return
            inv[item] -= n
            if inv[item] == 0:
                del inv[item]
            private["shed"][item] = private["shed"].get(item, 0) + n
        return

    # Everything below mutates the tile the unit stands on, so it requires that
    # tile to be owned.
    if tile == "LOCKED":
        return

    if op == "PLANT":
        if len(action) < 2:
            return
        crop = action[1]
        if crop not in CROPS:
            return
        if tile is not None:
            return
        if private["seeds"].get(crop, 0) <= 0:
            return
        private["seeds"][crop] -= 1
        farm["tiles"][fy][fx] = _new_plant(crop, day, turns_per_day)
        return

    if op == "WATER":
        if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
            return
        if tile["watered_today"]:
            return
        tile["watered_today"] = True
        crop_data = CROPS[tile["crop"]]
        if not crop_data["ongoing"]:
            age_days = day - tile["planted_day"]
            window_start = (crop_data["max_yield_day"] + 1) // 2
            if window_start <= age_days <= crop_data["max_yield_day"]:
                bonus = 2 if tile["fertilized_until_day"] >= day else 1
                tile["yield_units"] = min(crop_data["max_yield"], tile["yield_units"] + bonus)
        return

    if op == "HARVEST":
        if not isinstance(tile, dict):
            return
        if tile.get("yield_units", 0) <= 0:
            return
        if tile.get("kind") == "PLANT":
            crop_data = CROPS[tile["crop"]]
            if day - tile["planted_day"] < crop_data["first_yield_day"]:
                # Ongoing crops only accumulate yield_units after first_yield_day,
                # so reaching here with yield_units > 0 indicates a bug.
                if crop_data["ongoing"]:
                    print(
                        f"WARNING: HARVEST on immature ongoing {tile['crop']} "
                        f"(planted day {tile['planted_day']}, current day {day}, "
                        f"first_yield_day {crop_data['first_yield_day']}, "
                        f"yield_units {tile['yield_units']}); should never happen"
                    )
                return
            units = tile["yield_units"]
            tile["yield_units"] = 0
            _inv_add(inv, tile["crop"], units)
            if not crop_data["ongoing"]:
                farm["tiles"][fy][fx] = None
        elif "animal" in tile:
            units = tile["yield_units"]
            tile["yield_units"] = 0
            _inv_add(inv, ANIMALS[tile["animal"]]["product"], units)
        return

    if op == "FERTILIZE":
        if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
            return
        if not _inv_take(inv, "FERTILIZER", 1):
            return
        # Active for `day`, `day+1`, `day+2` (3 days inclusive).
        tile["fertilized_until_day"] = max(tile.get("fertilized_until_day", -1), day + 2)
        return

    if op == "DIG":
        if tile is None:
            return
        # Removes plants, weeds, empty coop/pasture. Does NOT remove a placed animal.
        if isinstance(tile, dict) and "animal" in tile:
            return
        farm["tiles"][fy][fx] = None
        return

    if op == "BUILD_COOP":
        if tile is not None:
            return
        farm["tiles"][fy][fx] = {"kind": "COOP"}
        return

    if op == "BUILD_PASTURE":
        if tile is not None:
            return
        farm["tiles"][fy][fx] = {"kind": "PASTURE"}
        return

    if op == "FEED":
        if not (isinstance(tile, dict) and "animal" in tile):
            return
        if tile["fed_today"]:
            return
        if not _inv_take(inv, "WHEAT", 1):
            return
        tile["fed_today"] = True
        return

    if op == "COLLECT_FERTILIZER":
        if not (isinstance(tile, dict) and "animal" in tile):
            return
        if not tile["fertilizer_available"]:
            return
        tile["fertilizer_available"] = False
        _inv_add(inv, "FERTILIZER", 1)
        return

    if op == "CARE":
        if not (isinstance(tile, dict) and "animal" in tile):
            return
        if tile["cared_today"]:
            return
        tile["cared_today"] = True
        return

def _adjust_herd(observation, action, day):
    farm = observation['farms'][int(observation['player'])]
    private = observation['private']
    shops = observation['town']['unlocked_shops']
    cows = sum(tile.get('animal') == 'COW' for row in farm['tiles']
               for tile in row if isinstance(tile, dict))
    sheep = sum(tile.get('animal') == 'SHEEP' for row in farm['tiles']
                for tile in row if isinstance(tile, dict))
    yarn_open = 'YARN_STORE' in shops
    milk_open = any(s in shops for s in ('PIZZA_SHOP', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP'))
    for order in action['market']:
        if order[:2] == ['BUY_ANIMAL', 'COW'] and day >= 3:
            if yarn_open and not milk_open and sheep < 12 and cows >= 4:
                order[1] = 'SHEEP'
                sheep += order[2]
            else:
                cows += order[2]
    shed = dict(private['shed'])
    inventories = [dict(inv) for inv in private['inventories']]
    for index, operation in enumerate([action['farmer']] + action['hands']):
        if len(operation) < 2 or operation[1] not in ('COW', 'SHEEP'):
            continue
        item = operation[1]
        other = 'SHEEP' if item == 'COW' else 'COW'
        if operation[0] == 'PICKUP':
            quantity = operation[2] if len(operation) > 2 else 1
            if shed.get(item, 0) < quantity and shed.get(other, 0) >= quantity:
                operation[1] = other
                item = other
            take = min(quantity, shed.get(item, 0))
            shed[item] = shed.get(item, 0) - take
            inventories[index][item] = inventories[index].get(item, 0) + take
        elif (operation[0] == 'PLACE' and not inventories[index].get(item, 0)
              and inventories[index].get(other, 0)):
            operation[1] = other


def _project_stock(observation, action):
    original = observation['farms'][int(observation['player'])]
    farm = dict(original)
    farm['tiles'] = [[dict(tile) if isinstance(tile, dict) else tile for tile in row]
                     for row in original['tiles']]
    farm['farmer'] = list(original['farmer'])
    farm['hands'] = [list(position) for position in original['hands']]
    p = observation['private']
    private = {'shed': dict(p['shed']), 'seeds': dict(p['seeds']),
               'inventories': [dict(inv) for inv in p['inventories']]}
    for index, operation in enumerate([action['farmer']] + action['hands']):
        _apply_unit_action(farm, private, index, operation, 10,
                           int(observation['step']) // 24, 24, 100)
    return private['shed']


def _production_agent(observation, configuration=None):
    """Kaggle entry point: final callable; no mutable cross-episode policy state."""
    configuration = configuration or {}
    action = _baseline_agent(observation, configuration)
    if (int(configuration.get('episodeSteps', 720)) != 720
            or int(configuration.get('turnsPerDay', 24)) != 24
            or int(configuration.get('shedCapacity', 100)) != 100
            or len(observation['farms'][int(observation['player'])]['tiles']) != 10):
        return action
    tick = int(observation.get('step', observation.get('day', 0) * 24
                               + observation.get('hour', 0)))
    _adjust_herd(observation, action, tick // 24)
    if not 168 <= tick < 706:
        return action
    stock = _project_stock(observation, action)
    orders = []
    for operation in action['market']:
        if operation[0] == 'SELL' and operation[1] not in ('WHEAT', 'FERTILIZER'):
            item = operation[1]
            quantity = max(0, int(stock.get(item, 0)))
            if quantity:
                orders.append(['SELL', item, quantity])
                stock[item] -= quantity
        else:
            orders.append(operation)
    action['market'] = orders
    return action



PRODUCTS = ('WHEAT','CARROT','TOMATO','STRAWBERRY','MELON','EGG','MILK','WOOL','FERTILIZER')
FIRST = {'WHEAT':2,'CARROT':2,'TOMATO':8,'STRAWBERRY':10,'MELON':10}
MAXDAY = {'WHEAT':4,'CARROT':3,'MELON':12}
MAXYIELD = {'WHEAT':6,'CARROT':4,'MELON':6}
ANIMAL_PRODUCT = {'COW':'MILK','SHEEP':'WOOL','GOOSE':'EGG'}

def distance(a,b):
    return abs(a[0]-b[0])+abs(a[1]-b[1])

def home(p):
    return (min(5,max(4,p[0])),min(5,max(4,p[1])))

def movement(a,b):
    if a[0]<b[0]:return ['EAST']
    if a[0]>b[0]:return ['WEST']
    if a[1]<b[1]:return ['SOUTH']
    if a[1]>b[1]:return ['NORTH']
    return ['PASS']

def plan(obs, hires=11, exponent=1.0, watering=True, sell='immediate', forecast=0):
    t=int(obs['step']); day=t//24; hour=t%24; remaining=719-t
    farm=obs['farms'][obs['player']]; private=obs['private']; prices=obs['market']['prices']
    positions=[tuple(farm['farmer'])]+[tuple(p) for p in farm['hands']]
    inventory=private['inventories']; tasks=[]
    for y,row in enumerate(farm['tiles']):
        for x,tile in enumerate(row):
            if not isinstance(tile,dict):continue
            ops=[];value=0.; units=tile.get('yield_units',0)
            if 'animal' in tile:
                if units>0:
                    k=ANIMAL_PRODUCT[tile['animal']];value+=units*prices[k];ops.append(['HARVEST'])
                pass  # skip fertilizer collection ($1/unit, not worth worker-ticks)
            elif tile.get('kind')=='PLANT':
                k=tile['crop'];age=day-tile['planted_day']
                if age<FIRST[k]:continue
                if watering and k in MAXDAY and not tile['watered_today'] and (MAXDAY[k]+1)//2<=age<=MAXDAY[k] and units<MAXYIELD[k]:
                    ops.append(['WATER']);units=min(MAXYIELD[k],units+(2 if tile['fertilized_until_day']>=day else 1))
                if units>0:
                    ops.append(['HARVEST']);value+=units*prices[k]
            if ops:tasks.append(((x,y),ops,value))
    routes=[[] for p in positions]; ends=list(positions); durations=[0]*len(positions)
    # Make ongoing deposits irrevocable for this turn; reserve their time.
    first=[None]*len(positions)
    for i,p in enumerate(positions):
        if sum(inventory[i].get(k,0) for k in PRODUCTS)>0 and p==home(p):
            first[i]=['DROP'];durations[i]=1
    # Deterministic parallel vehicle routing with a hard delivery deadline.
    while tasks:
        best=None
        for j,(p,ops,value) in enumerate(tasks):
            back=distance(p,home(p))+1
            for i,end in enumerate(ends):
                travel=distance(end,p);cost=travel+len(ops)
                if durations[i]+cost+back>remaining:continue
                extra=max(1,cost+distance(p,home(p))-distance(end,home(end)))
                score=value/(extra**exponent)
                key=(score,-cost,-durations[i],-j,-i)
                if best is None or key>best[0]:best=(key,i,j,cost)
        if best is None:break
        _,i,j,cost=best;p,ops,value=tasks.pop(j)
        routes[i].append((p,ops));durations[i]+=cost;ends[i]=p
    for i,p in enumerate(positions):
        if first[i] is not None:continue
        if routes[i]:
            target,ops=routes[i][0]
            first[i]=ops[0] if p==target else movement(p,target)
        elif sum(inventory[i].get(k,0) for k in PRODUCTS)>0:
            first[i]=['DROP'] if p==home(p) else movement(p,home(p))
        else:first[i]=['PASS']
    stock=dict(private['shed'])
    for i,op in enumerate(first):
        if op==['DROP']:
            for k,n in inventory[i].items():
                q=min(n,max(0,100-sum(stock.values())))
                stock[k]=stock.get(k,0)+q
    orders=[['SELL',k,n] for k,n in stock.items() if k in PRODUCTS and n>0 and n*prices.get(k,0)>=5]
    orders.sort(key=lambda s:-s[2]*prices.get(s[1],0))
    if hour<2:
        need=max(0,hires-len(farm['hands']))
        orders+=[['HIRE'] for _ in range(min(need,10-len(orders)))]
    return {'farmer':first[0],'hands':first[1:],'market':orders[:10]}


def _exp119_agent(observation, configuration=None):
    """Kaggle loader entry point; deliberately the final callable."""
    configuration = configuration or {}
    tick = int(observation.get('step', observation.get('day', 0) * 24
                               + observation.get('hour', 0)))
    supported = (int(configuration.get('episodeSteps', 720)) == 720
                 and int(configuration.get('turnsPerDay', 24)) == 24
                 and int(configuration.get('shedCapacity', 100)) == 100
                 and int(configuration.get('farmHandCostMult', 1)) == 1
                 and int(configuration.get('maxMarketOrdersPerTurn', 10)) == 10
                 and len(observation['farms'][int(observation['player'])]['tiles']) == 10)
    if supported and 696 <= tick <= 718:
        return plan(observation, hires=11, exponent=1.0, watering=True)
    return _production_agent(observation, configuration)

def _repair_shadow(obs):
    original=obs['farms'][int(obs['player'])]
    farm=dict(original)
    farm['tiles']=[[dict(v) if isinstance(v,dict) else v for v in row] for row in original['tiles']]
    farm['farmer']=list(original['farmer']);farm['hands']=[list(p) for p in original['hands']]
    p=obs['private']
    private={'shed':dict(p['shed']),'seeds':dict(p['seeds']),'inventories':[dict(v) for v in p['inventories']]}
    return farm,private


_REPAIR_OPTIONS={'fund': True, 'max_deficit': 50, 'keep_wheat': True}

def _repair_purchase(obs,action):
    # Quote-based cash projection; the other player's future orders are unknown.
    # Only small animal-purchase shortfalls qualify. Never liquidate wheat.
    tick=int(obs['step']);day=tick//24
    if day>12 or not any(op[0]=='BUY_ANIMAL' for op in action['market']):
        return action
    options=_REPAIR_OPTIONS
    farm,private=_repair_shadow(obs)
    for i,op in enumerate([action['farmer']]+action['hands']):
        _apply_unit_action(farm,private,i,op,10,day,24,100)
    prices=obs['market']['prices'];stock=dict(private['shed']);money=float(farm['money']);hires=farm['hires_today'];orders=[]
    reserve={}
    for t in range(tick+1,min(719,tick+1+options.get('reserve_horizon',24))):
        for op in [_PLAN[t]['farmer']]+_PLAN[t]['hands']:
            if op[0]=='PICKUP' and op[1] in ('WHEAT','FERTILIZER'):
                reserve[op[1]]=reserve.get(op[1],0)+(op[2] if len(op)>2 else 1)
    land_count=len(farm['unlocked_quadrants'])
    for order_index,op in enumerate(action['market']):
        kind=op[0]
        if kind=='HIRE':
            a,b=1,1
            for _ in range(hires):a,b=b,a+b
            if money>=a:money-=a;hires+=1
        elif kind=='SELL':
            q=min(op[2],stock.get(op[1],0));money+=q*prices[op[1]];stock[op[1]]=stock.get(op[1],0)-q
        elif kind in ('BUY_ANIMAL','BUY_PRODUCT','BUY_SEED'):
            item=op[1];price=ANIMALS[item]['cost'] if kind=='BUY_ANIMAL' else CROPS[item]['seed'] if kind=='BUY_SEED' else prices[item]
            deficit=price*op[2]-money
            if kind=='BUY_ANIMAL' and (not options.get('cow_only') or item=='COW') and 0<deficit<=options.get('max_deficit',1000000):
                # Fund only from stock not committed to upcoming pickups.
                budget=10-len(action['market'])-(len(orders)-order_index)
                for product in ('FERTILIZER','WOOL','MILK','STRAWBERRY','MELON','EGG','CARROT','TOMATO','WHEAT'):
                    if product=='WHEAT' and options.get('keep_wheat'):continue
                    available=max(0,stock.get(product,0)-reserve.get(product,0))
                    if not available or budget<=0:continue
                    value=max(1,prices[product]*options.get('price_safety',0.95))
                    need=max(0,price*op[2]+options.get('buffer',8)-money)
                    q=min(available,int(need/value)+1)
                    if q<=0:break
                    orders.append(['SELL',product,q]);stock[product]-=q;money+=q*value;budget-=1
                    if money>=price*op[2]+options.get('buffer',8):break
            affordable=min(op[2],int(max(0,money)//price))
            money-=affordable*price
            if kind!='BUY_SEED':stock[item]=stock.get(item,0)+affordable
        elif kind=='BUY_LAND':
            costs=[0,1000,2000,4000]
            cost=costs[land_count] if land_count<len(costs) else 10**9
            if money>=cost:money-=cost;land_count+=1
        orders.append(op)
    action['market']=orders[:10]
    return action

def agent(observation, configuration=None):
    """Submission entry point; deliberately the final callable in this file."""
    configuration=configuration or {}
    action=_exp119_agent(observation,configuration)
    supported=(int(configuration.get('episodeSteps',720))==720
               and int(configuration.get('turnsPerDay',24))==24
               and int(configuration.get('shedCapacity',100))==100
               and int(configuration.get('farmHandCostMult',1))==1
               and int(configuration.get('maxMarketOrdersPerTurn',10))==10
               and len(observation['farms'][int(observation['player'])]['tiles'])==10)
    if supported:
        return _repair_purchase(observation,action)
    return action
