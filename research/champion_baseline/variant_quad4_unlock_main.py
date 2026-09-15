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
    'c$~#u%Z_Bnas8KB*P`DK??z;cBs63bGeZlqKnMaX!+;?#WbX|BySuxpZrz)4UXj&=SKYYv%12~m#EBCTfBv5j|Mu5^{QYnL`0!7E{_yk1FJC_V'
    'y8H0&fBnyY{jZk?FaQ4iumAXuzy0^i|9}4QyI=nFm!CgBfBVZfUq9?V{PFvzk1u~OuYcYB`NNl|PoG|&JwLzvxp{qp-'
    '+Zxt^WoY3ufP89Zas>ho<D#6o)2UD@v8^=Yq!T&KK}H>j~`z@^Ud=gUq12r`1>C|KYd95*?h;B@1LH2e*KnV)L))|*^c^UIe+-'
    '(55N3;{N2mfuL6&b(_R1f?dRv8Kl}>k{q_0Bk6)h;pM4$Km#3$1U!MQ?^y&Gh54-ht{Ql|l*B?Ip@GnoF53^pq{kZz<@i4n(-'
    '23Torg<9nAD_N_{lMn*yI+3z^zC0>MC|J?uj{&=9Q(2TXf{7Ke9P;Se){;$lU>na0<SYH!o6L|tJO;W_`|0^9KL)b>X$&CtvI704^!U%I9S;6e'
    'd9F1&J#gVkH;A$kE$M6FW}R6-'
    '+kCUj7xKv7L=u@k42VFtMI0$vYDIR8RbdK^~=Wn^mSP*@`MkLp00yDEV4NW3;c!Gaee&yGSA_^x3R*X2V1;ZE~Y!K$MJsu@$)~Itvd~2**c&Pg'
    'cfk(_$EU)<5+(G`u^=ep2nZAOSpb%yYz77-hP^#m~s<Tsjk1jSMZySt8dy*&5C*1p7EQ)O**~y&BwYohaY}<>GLy^;p3-'
    'QKX$wl!A=}Cd)ci>E7uDv*n~lQz_lNTMMon}GF$q(zd*sPh6L0IG;_*{0G7z89^gO20M!LO*omtz*^3Tb(v#MZTIzJxjMfAaSJ!wE^W~p9Ffs9'
    'H)6orolrizMoAubwMXWjak<+e%lXiOX@X7YHu$C{UX!&PlY;EVNwmGn(>weY69gcM47l9P54k0qj;H@iu_oy;&q=j_6@VM!HGPI0mbTUnuQxnK'
    'm*=Ha|4RdbPbuIe{O5!)qpFTZ(^Yt&QtME+$;m6`v>6KPZi)ArR_c#CE^&MT5G#sY<rQCl4hiI*9st>UoCAmJup4a}+V!;igI~-'
    'bQCyeHQaQzkdK%JM>a;~&h!<)dcMtgJX5RqrQY??gg#FrR`4iDvcZL|(0P#Wl)%_OQn$vn8D7~X+rNRb9#S)>@a{wM8#o>>ieS_q{`DKvBV!7p'
    'DwfBfU`o<4v6Q)n8AaV(l$9QhN-lxX6Eo*cAHIaOXuo#bczP1PH*8s%h;;@e=>B&s*UV(*T4g;u4^)xN8n%ielJ1>7IhWw47nOi+ue?Wa^b)Cj'
    'p(zpQxGSzf}14=3MpSR%A~Wp)W*zE(E{R@_3i*6liZTSw)REUvzuwsWxfc>DSR{zCZ=!&isZGWY$h0fVw1V^@YeX+k}KpPw;F<)w>$L--'
    '}Rk`thT_X?ab#0>VPm-P-RTkpw;n*&P}T+F-ZUICDy!gxcA^@_?Zwk(qOuN`6V)?2E}rjL*c1WcH%Rf(RE&>oyV?r~Gq&pHq2N*z(3-'
    'lgbJj^meWQ{G5SjSpSR<)J31P)}ed6DaEVQ`cI~VGsbkZ<+9{%YPcZfe4A*fqC4~^Vjm}_ixdWQ5>c@C|zwuRj5y0(R}H-X{-'
    'iL?2BsDnvJS{RbV4skzaT!i=-'
    '|=rgF>HR?nB}r|a=!Wcw@Af}3i`z_+w9h6t6C0p=s=8S+TO=@D}Ok$NX!mkJGZEgT!#9_I>Bk>XQ`bBXNp2s4<nBCy&}zH5y@91cn9#UA(e8f|'
    '23@=yd02)P*h%+4pLnDbQ1_gG75T6D##UXW#7ZwiCI6gJ1U3u&+Eh|A&&x4g!kbgT78ra~^Er=1&G)D$;YHpFWU2!c#PDb4KTN2}9nKuKeZ<_T'
    '2BT8072*LDNW7^HPproa!Ns%ykw$<7%#Oe_zH>zm`92~tw97&u=qlYqg2-'
    'GuYdKkN<*`c4q|POLMt88>==4)@FYT|~DlgKWKw#opd!*sAar1otVTPBdhse^E~bKdPy|`~%jq6YxroeLJQu&ty-u8-'
    '9mWnsE^9B#)!t+{1bR0T2R8YVKQ>e}5CJcOuuQ24Fx?6`j}Aq`p2*WprP?1!`wK4eo&rZ&MZ;fG$O<$8CF{mex$%Y~a!Cq=(rx<BR{YK2VSmbK'
    '3U^Y%l(oToB3NtDa#3f5g_&`P!DNy4;=yB!qW0T{Iz50;zqo(%~Hdg@v%V=hhCq>>WxVIS)cgcm>Rv;qEhw0XKc<@eS+69ADdP3iOz(T59{rUR'
    'nq>Yb4%X#NKrh7q1GD3FeHWpRI`So#xfe2{mZygSB!wjej{sI-'
    'YeDrQ{Ngg9+dcK<1YUNKbGM`kdGfnCsvg8HmtGs=UDyM$jmjw_tos;c-RS0O7z%(qeZCu|SyS(O<U^aYzE%iRqZ#Y7(UG>LPHd%V^jv-hsZ}8-'
    'E?n8JJ0+OdqK*Jk*u1L3IOdNy$!J{&9N2P1)R`(eG)TCg!*0ioBJRKyy{u@?a=7$!4pb1JUw1qEvSqIH8u3keG;qv5QWjit8n}(w$eDrypD7dG'
    'Srp|9N(RN8fC{Xa(Ma5{H&6gK?(tD#h?6^4H(S07|GFz9FJ&f5afl#DoVUA*T){*(763vx<om6~z<b+<o*HxG(kTBfHh8M^=^Fl2EW{g)wcXg^'
    'Pn*BMChn7zt&mVDzqfD>WDaZ{kKS!%^lFd$(9!-J7sxD4rdulx|373sp^SetZ$7DpOOQJvVuazOHh;Y#cJtBe#0iwslJ%r`tVx9Vt2Lz!*-'
    '#Y9LFu?re7NVY^)sjf6v$#TJs_m8_qDV?xQo;ndl>2}dh&r6#b3vHHr1T7M0bT1y~m-QW-Q$q%tlbvCa8+-Eq)CSPM>aW-'
    'a)k}xB3I}Z*NO=z9Fl6XMo)y54)kppy2^1+?dY17JvDVFE4{!3+w@#uFUqXJDKIlYc_MNWWE)P+j<7?~}@B6xGNdIay0x^qvCVgt;n<tF^4caB'
    'p5<1qp85t<pRB7Htp3Z}1!U<ysj+xjcLawucXIyWxpAkwdE-'
    'N48oDmr6%)5)y>hq0$pYSy;d2@_P}Dl?8o3l@ShAa&k&uvlUEi{;Cmai{?U?VyMEAGjSRQf)yFSgRR=vY$nBk!qZqFIw0*%tCp6?L}LEtF(t*6'
    'XzL`$Cc=Ix<&^QN$bc01`5Dln}f=NJaYxEYPAwcSYlOdb}Sppd*v5V-My9I4-'
    'lL;qD!d5m5qp#X`2SPj8KZAt~fK$oh?vEH(qH}gcW%u$46BhWP!**QB-'
    '?#L*Y!5n&iba%&d2+MYsyD2Qfn@N}vEM6coPz7HX|JNtSstMyVR=mCJL>i1s2vI|_6VSE<N)MP8h5q(khLN*oDwj0o2S#tsvvzl;EhhFf>3yU}'
    '<nt(wUsN}gT`Aj}r}0nraE36wUj&-'
    'cnpNCAa>sAvR^RepYY0Q8TlX`<;ILI?O$8*h=U_;AJ+#l*HV062M&WHC$hAGwa^$fOG4N;SdY72nN(6Je<$K&oKQ`TbxM3@_gVN(XlnSnQ=KPA'
    '2dg>Kz{yCOZ$Y_RseLP)HuL2(k6WPya3U#frftwo<7VuFAlVxDaQIvAoN|my(!Om==Fbj%>KOu)j1eN9J`J3!)hjvA_)-'
    'eM7iJQ;s=hoy3PL(FLYXq-'
    'Q%Zek(*+Z}DYV<JCQLQ;g23sUo82wr2ZZzwoq`n}fSu=bqsKwyRcfDagaxN{$z=k<JRND!{Va+#%h4oRu(6gx%h6ytFv8#X4LBQisQk;62%OsZ'
    '}IQ{Lm%pl<^iSA>oz}=k0*ISsPkG$5ZR!3&*iNY?|jFygQj6OyG<tl@RQ?3+y7ga_Z|GExJG<ISi#1&mxlMW!D6yv@>-2Nm`ODfW-j%2skNF-'
    '4)MMaqAnWR#!M2kiTf1v)VxAv~2=}=hD?VMsr#~28VIQ80ds9yfsbTeMi@pI<HI^RmXrUu)AWTI%#^q1g;nMUiaMT3%YL$XXUHmz|aC&*P_;$5'
    '}H<4aBN;acHW>%0+tL(!sN7}Lz>M69sBESSHovz23a#kUxj*+vlA~E7^S7{A^d8jMXmI)Itn(8AMCTsGu{@LoQ!z8*K3ExjWpO07P1^rZh=gvQ'
    '+V?v_R{ev>d%9dRK2m#<tn&NOnz7F*xGy$Khtp|YBKwDWyb*oD~HAxK@uKpR22QXb3l8D=6R{pkYkZpD+4?NnEFUjWdj0MHi{%!|3liP{<u0K!'
    '<;;V)-^;Nfma-L)Y0V`0=V<kwL`J?!L3B(8jUr#cO{3d7n?sLH5iFd7JW={T{h1k@dv0d5{A{z$~%V-'
    'ybDQuCU>w)7f33gq2x6zb>N61By>XK<f(cB{gpJiDS!jkFHGl$$6+r{L94YbUW02Z4JDOyKoFTldQ;;dv^aBqyT5~11_GDAC4!J%M$OiCw`AX8'
    '3q1H?RQ}F5&UE3AyD~bE^s2JfLNK~5S^_LGKzfJ>@ytAntXk*SEd~P|-'
    '4G1duxRy{U1k#*6GR?7Rljj$LklgvP!m2BkG6u$@7@iS{63G213|SMfY6go;vxsqc9KGvAvaFq(b;gIg-'
    '{5n)98kej#)!<_TFK!0;V>A=eher1{iyeITM{}Tp4YzXQ#{aNGoK8goWignc0T8ZW|Bz&e9e<I7QaV8>}c)iCLEg(dmq8cIF@-'
    '&Xuu2!*7)cn#;I>7JXp{ffGEIHnM{(iM+-'
    '!lycNKcmg>Gjd?+jo4n+E#M<^(BU<C;6|LAYGFl9v$G$wq<tbdbGZ{_?v<nV>&xF;%PpM>=hNBx}BG%0&+3@Trg{agTlsX0qlY~&lh(8JP=}zS'
    'h3`U}qgF8ujnS4bb?l$Ay>3Q^-x)<-3NI#KUe?Glk{G$%74($f1zalvR)8oH;e*W^bsRn=-=%F!r9m(&-'
    '`5C$~!!LiA0oE#4y4)4E+KURwD1rLFIwDkt2raN*O<bEnF%%7v(J6C?L|7Z#u+v<;iM<zJAT=<*25=?{JApd_R-+LWJa-'
    '7@(2DrnAtJk7W}f9J`CLCBIY!g+rSk6=O4Qy!z7sQ0HsP^B-{R6@RegVaIZZfcF|z_x=zv0*qAuDDKCqxM^jO?%)-'
    '_nHD?T~49EHJweUmbJaH{omkpgxZK2ajiQBacl;D`54)i}|XV&8j~tVgthvduOiSWt*vF5^XAu3Fdv-fo6&1?H<8hjT_B*EMo#<%pwhR0Ymi#('
    'gmTE;p~92ENaM|K@qj;{kP?Wlr97^n9$n5#{j~qM|M;r94Bpd4fR>Y{X%$<#ra65bUO`?y%t#(-dn2$T*L!o#2X4Boeh+dR}Q-'
    '{h0T%a(P2!gz6FHQm1HQy<A0&4tBEok&0mN(k-jOx%I8GHf)3JnYtV>1Le4xhtsi>NC-};SFp-@okN-'
    '!>oU$ueyw=R$Fb)Ch(59clOI;D#UlZ5T}8Q#GC5AQ9;)F|YdPrYrZ4(gj}j=jdgbN?P)E~TF(Lt>k9Ld)@^@c8XUQwKK9phV=of7u%WU>I?v2M'
    'C?|#aFzI@YS6c(g`kURA5a_ecx5JjDYDuZB6MH^Bq6wkX<`y0VQD|=Vz?M+?7y_pVfZD3_j;BCA=NU@=HM=Zb`X$d@JF8LBzJWVX*Yd1M&AR?_'
    '&Fh(;sQafombbi#rh{jlhF)PV;UtdX`6BIF3L&zB~rxh<fOo1B$7`vS$^>RHUG<h)uTE}3`CP}Nm(bFDPpyS>>(Ll0J;4VRZkTW78@p*Y79ds)'
    'endViTmju!*zsZj+#XXyvOCAFi#mSX0f;G-f!YGV8z&-Fe0o}e3Q)-ylqo^&PBUhm#QZd6dPKCM-&xvxtpKG9NDDnZ^E2sB(IHv`<ymxg-'
    '#4dNo#ntJ`Q(3a}_B#K3FG0Aq!(Xgw7sOue_swPI<OdChx+2mLm=`M90OYOCfL0M^;#P@8)2grNIp9XHm-JKvfvTdeIH^2saPvsx6#!D$X7lWf'
    'aZKk|3@DgZ0BsGWB&Ce19Y7uS0AiW6S5pMII<_h<lG80IT@12P6Hm&2Eqfjqfcn*t`Z$-q45IGVWI&OdsGIO!-'
    'e1M0vHxnb1z;<zw@3lyWao3qdf*z)%Q-=5orxa%iM|!4c&{|P$+kBTeH)s6SOW;X)iiMR&IMBqI{2v?$e8-'
    'PFrkG>!ya4=%$Q;(<M6DEg1%o*<4)7CoYGW7Ej&3$k+us=Y2~d(wE?DwtV4Aty=6r${nPtJ_0+;tL9H+4G<V#mv6-'
    '4VWSW{?2L`sK+^KUB{~pR*U@XG6_J#|YcX%=>>UEq62~b2iRUNA0k1M`JXsx}g3n${0JLh3EQpkjLZ;Mh@LQI_eIS6hqNu(+TupG+PuEUr;5q0'
    '@&&vv)0o5*$n`xS^Vjdau?IUEgw6La+@q6#XXsMp3)Xt-SPYs`eW9D$-3;x=ubJ#u;!Ri?ZLod~}=)!@NPV0TAWl<U#GO}dynS9Z`f#HQlS-oS'
    'A<C=U)1ZC+)dCEvi{a>bGAaTM~L(O_b}O#IPaRdjfezy_H2DbsjA+REf%v=nbGdr#)A<mF@v+)eaZUm+Oz$Fd|75I<PE27-'
    'cXYRhEScad}81EIJR8|)2wc-2<=0sZ3vJS3w{afvCOs5fsV!{4Mm{T6+6L5G>BlxKA&Y#_h7CMpI7)*{ZE5`24-'
    'xD3u&5D_zXtt<}*uAhL0Jy#-'
    'Dh5KuJ9#xxt7|+9*x0gOXNJlBWHVibr$4Tnc8Mh3%YVMm)jIyH!S_l;pJ(xOJo6&70rpMutM*{pRboWI*tmOvC8Wb7D0q8{(*lanz-nK?#s{;w'
    '6r~s}CLPu7}bSy2*-'
    'X0Eyjs@b4WkpBUCDB0~m1tXc>Qz85jXsSok8>%KMtAl2xzJWG6I|YpmMF1(6x3Hxu}HAqbC9O0`XsJ0J~5pFu@%}*O)tf%I3tif4j;)GpdJ9`0'
    'ay#e(TdCnTFfs#1T+#rZYAWYMPkwlAf$UHO(C<jiOE)Lea_fC%Bhrr%)B{|s?s>IgfYOXf|A0Wz;63=y&jUoqtS|b7QppOb5yRjf^TtvE4pm!#'
    'w+^>s;LU`SU%9cq@kFq=>u&##*)?Lkd~j!j3}4y3{)BCGTcrOYrtvafy!#ckyB?Hj7Aacwi~4fE(3opLW1P|)n1)%V$DjA^eYS;j>-'
    'D2W)|}CM8QLO4q*g%^608vun0;!xZz?WgLz_Q<m9Fbb;I-mk-i6VFiKjnKNL>yVN9_y^=whnl;btcH!1-'
    'DwZy`5&oY39wSHfX=*)^dQw89&VM4?ubP>U$hSve822z>Yg)oht8et5y$GGzQm~J8C23>$KDjl8?mZ+iMmsQn+2pJi6-(dB#?PSi-'
    'S<*n*jr49Kc?~uMG%$3H1*jE8U|Fwh6Evw;HUPLF=5<~HW404ginnhKCE4h(1oHzG|5s0R>&vA1aGFVwlO+fJ)gyzb=p84w;`h(+hX^If82`RV'
    '<vGX2WCfv{GNDr_avhBLMg54)*9AeB(>a>}NAm0k<$P$B6%+c`U-'
    '0$$$B$p1QN;?;k;z|`S>@xMhGS6WlN|wJe4fQU)(gwqp1%7Ivn;maHW0W70A)azQXOWGZXB~sGg8w`Wn$GGdfUpWTml)zVq7~YD(kFu=1NzJ(;'
    'BW~g)yR10vlNU?e5A_TuwHw<nM#^(G(=fwXqop6U}5(T4Tmt66G>;J+x}A6R_~A<?Tv_^mzk1R1xHouBW$^c<bH-sn>vh;rI>M?C&u8MO9?lQF'
    'q5YM#C3}#*2WSYJHq~&ies1V>Ykf`ZC?m&mkO8w;VV+ram}`_{6r5B6X2sg;AKJ{t}Q2h#Sx{Kq4GK>k7~5cWKD4gn8|80To{u-'
    'mL9bEj2M(WoRb5x>MtulE^M$WuR=t^?bLLQiqz=dA?$Y<)6AJM;2WJ@01nEu)rExyQldDRiso>laoWRK?>gu2pOnsq?Mx_i~?#bZc>HQ9F}!Cl'
    'l%$b{Foi-?pl#yDu^v_KFS;+6fv@t-asm-'
    '4yczR9<xlPy%`4}BNoXxy8=#$!g)S9`iJj^eXlY_qvaiziH@oCnRZHL3^=jk%Vaq%Oo*zHv|7FO7<BC~iK^G|-'
    '6Sq2sbj2iN>tGUUMX4}Ofkx4RD<ZU2<(JKm8DoTg*QXgL6pcU6cv^*^^*4bb=@R_nPCjbIF>-'
    '@=~Z?#LGr{>X?!(+2YZYYM{I2`7*$1!DU;{xsLR`3SapUJ7lPJ-'
    'UwXgFFs&-bxRP&_i<NwIcsL6DSiF>cMIoILWz;TOEeY%_zkl=YEt<QZ0OP*|lQVAG+mDpqK*~|pw-UO?z@VFzJ1kmH`Y&9LGvy6|8t4Wzh9x7f'
    'noOd0_8B(`<g1}=YSduzg=o5gb7y>#IA4KTM4R}Pdth(8xw<5-+(_Am`j6vo+K67!c6gc7ob_glg0c-F-_k-fk`bX`iXE9~AX`mX1|V6LESa=f'
    'Q#sSh&8ig`(&8S%NzRAu0>GG1=oEZC7Mb&Vnn)HME>}T`VI&D5l8DzLxYe)pVX|gg9X=Nrd{YViDmq5wX}&ypT2V(DT8qnuT!b4lr#I;+7>cNI'
    'CtJFUxiD7;WKe9l;G>0C<B!OPz9laNGo33kWaxKEdXNph2jD+4vBid|`bF{^I#U42am;r-NF&+QRv8Zk@1TQnM?VFO-Mp19o=KTA!ZpVyv`DkP'
    '7C_S}T}0>f#$%8ag!Cc7%3S~%G0&m#jVcYVa|~E)i_%%G9y%w8EFxo3HK98ja~coC?+o;uBMetxWYc`@h?I+4%bWDP<Z_JhRhXew&Jk{2YBQf('
    '{oR^PmOz|-S=$L5p>u-7&Hb~{eD~lzb48gI&{Xp|w<R#JB~k&lIV$B0^^a#RUa>c-'
    'c^4$>Y>`M}Vt52}fp3v=KV!(iLO><=3VdNAC^oDtywg@0U387OR1~Z<PAc*3nk%<T<WSFK2xdi^z-'
    '=?bLP624Db!9EKZSCltp(O1hC5{~VeYn&r7_{SUyrhNCD<H$T(E~yYF@_4%)@(=0tdP}D+*XD(p=I?+*&f7U^904QSy^6c?<M36RXs7!gAH(dZ'
    '%>*z&0t++NzOQtX-oV<U}Y@ii)rt;z7wuq6iAm#eUOU0gvR|nZQKm`|DJ0TzNaL#-'
    'eIWQYQXzQ)8k`rL;xd!0D3n%3+r^K^#r|Jo>sSs3Gf}g1}yS?N~VHs?{WLfoo-'
    '#ELxU+^Iy)n*9i>{uTEuz;_1)`sVeNOlSb2h_OyaD^$*|(rSiUIx}RIwx=;EZ?NwQXuWXJxwLyO$;|Czj_1^4Xp~a#7LR=~O1@7?Ue!vlXtZds'
    'uc~U^s@^kB;wl%HaAmZP&8&(xGfJ#(?7|>K{B3<&nJ=seHwKo38Td%jBqEwQ+RmgwK6Rc#AUlb6l2N!0>wn~eueUvs*Sm8uaX=X=N$AW0MA$>x'
    '{3woJGkeuvH-YEnliWfA}-4Y&WDGh!WGXkL>Fe2J1t=hhLG%HJotTk>>aYL8YY9k^-pXjw#5JR2gC}llE%N(}GaR3rxJ&DO9>`3t{+-'
    'PE9s%r5>Jzo<ls_2kMSBk}L;S7~JAwv)OMkX4-'
    '7g6FlCpv_`{S{chM@25|xsjFe&{X3VY6>e4$Y}G`>XJI1o%*8!167vNDqX9((yAyvx%2`SgaovcGaaN9;;RSPL0}DqU(%|ltrR0xpe|rQO-'
    'YMVFdEPUd9KqV3)N@qyy+TZ+Ybkh?Hxf>humz{mrZJX?pxSpy(=?iby_06RdvJRD52R0^eaq1QwH#6z!yz`+dx8GGozB-qQ<GW3)F3a@2sF!Sd'
    '|;st0&9F4iZ19$On`hfX4fAW2jCU4snvL{x9Hr)*Z>hsARQAA3=QfjZg8LB1AepuHgVsPRR9El_Uh28&>9vq$vJcDT2#aF4_1l>yN=To5>+Swc'
    'NDRjt`3AE`!-$i5Hs@7EB;0CkC!|xMkJ6X+c(^WRwUgB%maaxf(`1Lvsi$UZ>S5Z_1B~7h>+DpyA5~G6CKX<ESeJxdoKgiEg^d-'
    'ewtN3_QXbA2Wqa$c`h`K^jkMkI~h{0qFr_Qe^*jh!I(hThk%wxuk3#nPnT)uv1C0G>@NWP9(P6DEvLSH7W)?iwxa?iO}OiOA>*sO*fa}7$^YjN'
    '|5G`DhDHRp-9$*Bk0v5SdS_2v~}E)Wfqt@1*rvfI*90*bKa@36wNEh{vhdrjErM?&Vb-TOqSg7=Vw$D0@)vH9aZoPN|=zzI8{m&nOMq{iNaOO3'
    'SYn0^Q9`sZdDKp2AXZkTXa#SxnrJ`-lgrE@Yf{e!iDi3-'
    'J8x!VyI0JKJC@+S#~AHlT_HwLqsB3ij>*n_LC&Y0Wf_!Wkgy4XZ&Y*Je;6)80#7bePhRNfKkGlPU7jO`s;>q4U%8ZNVj6AeHz)3{oA3ReMetGW'
    '!m@3#eC%@`e0Bg2_5>zDzTj!J{Qt{obLtT0g9Qxm6SkAjrTz6`&v~rXe?mt5qo|z;|!DMN094kqav(nP;2e9Tlz}Nz#9G4DYCg0$R9HtPSp&Kc'
    '<n%c^SF7B`L6*dx;rgF$5bS|jNniN&gDvdDI=}txbr3ES2I48@}Bp2vIA{w{(?D!tp%Pkex-'
    'G4I)lf2CRPn&NAN$zQIHiuQ|}MHJ!!k~+dQ8K($Ebm(<YpohYA8^>+cu`vy0q`vHLV3+J}y6+QA=d!g=DbXdVD>*1ZFIdzvgVTQi0bv~blJOX}'
    '6^w$m@$X_gE=wI>wR;^j3X@`EU~XD3iB44q4hba1iO;vB%NrpTm)0lj;pjiTP0z!XyAQpyQ+@gLTmB|c(6CKp;ymj`FCl`cc*k*v#YneBbBQgR'
    'ibV1pW#+{9DG18Au?QEIiJXLN7KsA(5@KWiUGE4ekRlZLQSr0C8Nv{GUc9Ew)|r%shgdAFWfx{Mh(fKwSr3@&sbv#13|EQkS)0s%900>Wz1wp}'
    '=!Rj7=aW~SS0oSAT5D&nQ={kTg@j*EY6v_&`hqx7=d%|lLmqF?Z`P+T-'
    'REipyo5)fnr_5tj+s?tRQ1fck8(4&<_LBN>%6}gq<?vWQ+C7_Xa2hB-Y#@ceTG)WQ?t$-'
    'S$R2DL<yl^=pJ>@ldkWB{{5!_2r@e<u6O~okRA!9`s7ANX^DmN6Y-'
    'Wh%`oPC_r67$Mb?h0Hw0fcQ<qZ__umvHGX2fBAkPm;pw7=g)hf66mEKV~>52nR3Yu({!M7K+0@M_aQU?NNO=s3}~@$mU+6S802^h996rB5%A1d'
    '>4gxya$-Cj&#Z9z&(kOB~p8<<!Wxz(@-aO=`^tXvrPyaUws+_m6QuXfk{*&sZ3wZX32}6l2gm;OVEh@_zPzu&)PAZs%k<(wL<g5#h}-'
    'jgHGP^Y-ZixAi^_93aNr{=j|$$(WcX$RaIFq&r*qcvXtCLUl+A@Io5|4BT9<M4X?gU!mGic6}gRX*PAd-Ry!_rj+p1P|0z{+98g{XVWy+*8Z|!'
    'T<kj+4#R(NbHf*>EjlX&m%^5ZzM8`?6N0~DV1Dw*qwWLPCF!5<U<*$C|U9xVRp=L*g#WcKDM)#ZMamxIWAWM@o{7m(7`i;J|AMB#BnQFFi+jP)'
    'Y`5--Gri6fnt&&DHkFMn_3L#GxLtdNGoE0e{;u|^=Af4iEtGw&R407Bf$?_CerDh{}0+q(6^gCM!aJ3|4y|@@b=qy&J&WyDpWTkmix~x+!znSD'
    'x*K*q#tHgW3jG_>5i*;+cTGVAiTa0y@=K-'
    'r&r#A+TsUeG<PCKL^h+oQAs0=5CSG81$Po9mN0BHJ43T+lvQ`I@zd(y7EV;BRsxJ4vM%*awTsERZ=y@GosBW{}@Ip&EZ7?Q57<0M~}Ip<U?Piq'
    'O7LxDkkUR5kq<t}L~V~;MduppcOuH0G#Cnw0JiJBTqB?W6_7MP~<iZ!LS^P!rT*WJ>Zl_@SUFri`<0&(ai(naMngi=urV-'
    '!RiJKBdyt=$svE`Zi|A}{Z8#ex33idCcUi*?1F?SyXStQX8?e1^OlmJ%9qp?H(=oH!8$BTgxoW#-r8ENkP-BrVC=bd!Z5==Vu3Zm*dh@)pi6+~'
    'sRj##l`Vb_gJ7^Juvw!W7p=^E_3sRT7iX^^!p?j8Q>ZDM23#n`$PoB2$@2eRKwZYcMw<9^QnD={}uaYmZsb#{_x>$k~A8-'
    'l4I9`Vp3bqLRzVha?pr6?W=ml1%~}vVNDXB)d#{nj`dEr^fyEsdqh+{LsgyeI<rC*<AVlb7bpu7J>a;PxJ9z4R&arkY=x~ev4z^>czN-'
    'I^?rM4gDSH>{Ug2ez#>$BiyWJjO=qKpyyqlreDcWB0%EnGsbrxG)h`|3X0!I;Tz<%i*%cr)^<=I#By6bXCMYKRX2CjU}jfF7EJRWnd9F(TD)XY'
    'U~{NS7v*fVOeC$}Wm8ax{iFU;_3TtVFVqq&qiPCIaIQRFGE~f1_HdD@Pl}zA^chBrXbiJeaLWTj^-'
    'aABCdc!C{A)TpqyMsaM+G}T9V$>d>hS1LrJ4dIh35lIbp$?<x-'
    'THRD%k#5b%{)W@+y#{vulkd6<9+t;M}VleC5KrloBQCmHxWN@9e@xol6zq6Fi%a*AAy;$jNUIuwp@vcCC8KfCi=W3c*Cmta(YaD7OS=EH*mYsg'
    'f700+^^|gKiE5F})X|SWN@(kyO^pT?{`9{g_#V31}vjj<VeePPGhx6qy=;HOF-Pr3WD}ajO73K-'
    '$JfIy~jQ+u~Lufsp~h>Oc4z=`ndtnUug%qgC08l+>o;O&`1?2q-GO@*p;4!&;&Q9ia@#9Cgpjr#?SJkeIu0P*6i%Iv<ttYF}xcJed!;A1XhCl-'
    '25xjiG;ua~fuA#>FuMDi3)CQn2CbfjnJG#Z%-'
    'aW*2r30WO=pTb)=nMt0D$=Zf*&`aC(;htFA#3hqX{mQHpPaA_o4e0~ML1lMahJ0c86@5C0)ER(18FiCC_miL_KS1UuUcR`kaX+M|A{BsF~Qcn@'
    'WU`fXtQht+mwS!gL;+5$_R9$Un#71Vnt8WQS>mnh?@?yDx0W7$pwq|-v4Vqq=s$<)ejhZ#Ah+0pro}<IoB3@LtBC+6Y>2MXkzj<P2odv-'
    '7VoF=03l%#{MZAPc1cEd^n&5;+;4Qn&dTg&o7n$k*RA^`9)8rhltJ~wD5*ca<a_35G70h^&Ay$A9j>Zi=8%h0q18{=b=6N9o8WNU_fhGk(%om!'
    '8Gm#`)P4d<h{1)W(jv+M3Z_n%cglxJHX)5m0OnE=gY#llp_q{~RQ%-Mao9v>-njad-<;)nANG2V+VHcE}9RZ8dcwG()fw5XG<Z-'
    '7tovK>+h_NTRynYI2;;LkMVq6MfngV0efNVSm@ywvcjTHfuX*t?O3Zu4MoJpV^m_CABx^wogaMpdpBo}{gJ%amK9u-'
    'qi5*gwXtvZio{!x?XYQ(SB$O8BJtXdrm^Ui{Tw2*=mtPhB^rNIYOh~#a!rX|-'
    'B549RpMQpGSh?koZnXL1ybEY`X%rEO|t0`0fl_FZbuL@p_N+y@FME4a3Qp%5l8V5IhjVv%`_L`7muAUX9VNj7A#;`su>Vm4YJbF<axdR3RNknG'
    '{7%;a@syQo)4q(tF$v2*=Okd4n1hU4a)Ru^kw)!Z)m^aqM-'
    '36X5kk2tUsT1Yu)g&3+61)`9)b^46fMQQC9iui+ak%=L(WG2YoncDToZ2eBlV;`rAEGwxN;`hs8uxnGywat?4Y`Zk&X2mXXH+L^`w*I~DH-'
    's1v>D%R2erpzt4&g|h7=<}rY#D<p)VqmAXaSu<)=>(8lb{W@iN)T?c6Z~yGUilp__9V{symS<q@#wp56WcKD8>vYMR{VNwuu?6tqjoSsf0M!8>'
    'sg4t!lwc3W1aD0@KfZgt?xi?xuV(6xp_#!76^J`I^$`K=B@>r}n~JpCjc1c9c&j>OeoK<XxMQ`0M0uFX{==vG=l{aKqXu@P^X1me6fvO8V+50E'
    '3sF94}XX-nab{Gc1c=^<h4(hBgcXo6lhRbho^q^G(AYsqRh7kkHeI&e<rL@3(P4t~AAi>tZMN_XCo=g8j$RawfV4?vv|Baf-'
    '3#<7~}|2x5T$8W7X50t_q;Z!8(pk|i}LDXXuu{DlmbjGbOaBz(XJKzQs{1o<UIpG1hq+<`rH3LW2q|R!J6u}5PEf=)z%ZO-'
    'T=$mnN3iE?C@OcGFVpW>bAdC!mJr;G&tN-4BG|S4$Dk@HA7aJa-OWq~yaI|0PC5E4DwfR<s`Abh8pom(lZUq|>6F9zUR~y%)k=WP!{HJS!jYF^'
    'Ds|t$rb3)&-c34#y0LhW)0|$KWh<xa*(9`!Re(~X&UYBY;Dvrfxz%bcuIY);Nu34-'
    '@y|!V|4rP|si^dWTZ|Q_VebX+jEvZl8D!HmQZMs^Cs+$#3!Zrl_r%%s6ahvxVy|q^v2|97W+L85zRH4u5@^66aR?_%DHKxhrlfx>W?3%#PMQf;'
    '?VtBvC#m>4&2Us0hJ9(8+vh5uJ<65&_@Aki9`GFvN68THuYKHMh5L4)6M{;xQ9dfZy3WOv-irP6aB$L(5l1M}C@ij8s5<*=4g3K9BDDo<Uomnt'
    '3#>ZL}NhPwWglpXJ_4?XmlbUXj=qt;Hgxaa%uYl}43Y`abI@3jR@=gVk8?oQ%%AJY+2J&1gb$J?k)`c=I^qM1Lwg3(yU{=2=%kIe&5~S-'
    'BW=^d?fZ+hus4EfE8Yp1t--w5<UyWpskEoqPZDG)qI9!wHYI8#L0#FtO`>sJyX?Ez&nP~Tdc+UZrXQ(wGzT{y4J22XG5#tJdW+XR@bI?9suDJg'
    'G60D4{tKz4^i7z#R8(rWvpEIQbp~*56iaO)$FvM-nlDx9%iecf6IPUM&rUmi=83OdLE4ExoabiFrV=a_RN1L^l&WdTP;)13^B2G$|K@h>t1uYu'
    'Z@A~@u<HxVhtt9nCHaYdLb_=RE_e_<YI1(8j)T2J7n(84~Gqylx;n;BomjxunuumH}_U<e=mcdr<*|<|M^(uaNJQhQpUWPN?y8G*Jq^LmLyXCm'
    'LJa4Xwu7&#O*3WSm`mRr}$&icX#zp*s>b*OL-&GTH6cQ8od8z%Qvdt_*O;9;i+mA-h<C-'
    'H=`+r|dq;iJbHBfgq4fvXL{B6s+{satKu5%HA7vX41yvClq(hJIO%y}Jb2j+%qc^ai^9KsRF0!u@B?UKN%Q@Wt8Tz|R5x0eW#yF!(1>f3n0rb5'
    '8`2B*snAH-=Os3}j1+{H-'
    'XYBxkdspUDPQjm~J+N`Lnces_kYUf|09W8rOX%VhMfoNrrm?pNf0_c<j$AM0OWVi$+K2tvM;%!_f&A1Oqia{#7$wozU!H}q}l#%JRqr1~M4u-'
    'Vtj&^{g)f6;!Fdosip}mBvt+MJK$`j^m+}`1DY%sQTtx45*0mLw)vTd8ZAr{iPqWn{|u;|$}TAStpk@lcUHbz;>Ts<krbQ$>_fFW;+vIQ0+%#L'
    ')SI@j=`W<lx$){83CAQ|wo7MG_MJ@sN6BRq^sf`E(T=N~ULCbry_bJa);v}F__uv3wi?DVBCwjNnOl<#s0xRzj9uF>yY-dz?T9vlGOWE@vG5Mc'
    '`(Hx#FO-'
    '^bx0ftwf`DS7_`h+J%NL}bSiw?dPokBhUMz<MX3l^%@qp~k*!B{!4XM%V8qY?<<iI`3W;Q^jy6pjajUEUOE@At+pbkMz|wie|0f_$IB7)aW!ln'
    '3tn@1pwEZYjm?+*JPT(^_IK;Fx#p`{A0s8D3F_2QRF?&R~&X{n~ctBsCS$9q1|NW*ImL^(4lhKst=e`9Bz<8ejQYCka-Yk%vFKGzEXA75t<872'
    'cpbPs3FASEdi<fa`xgJPiRfbNg2DvmVm!Ws!w??k8*CX44^Cp2S7{0n9ksZ772(v2+O5qw(VE<vPQ9mVeTY?R)|}_)=cYq8|NJj=a-'
    '<T5oIqak-'
    '$=^5j#=Zubt2y@US`)H&@V|Sif&?*gYU(Aa$*)0eLfuNn&rCWz)j1F9c*lYW727IbYqf%K4S1ds~oOuma$i#5Jwh|1?M?jfY1v<+}%J;gt!da4'
    'E3m0rkDA-^nBo7aVxFxFNf`F?-'
    'f8+^?5wuNH5ad%?&Yw@k|J5Kj0|w66B|jdE%s=ZO)zO08^=Fz!&SC;5_PSy;Wj^=2QfnA;m*A$u9FVq2F{Y5m1NTmFf}cI8MG-'
    '8w3pDvmx)ERLa@`XDyfa#MEhZ5XMSzT9?~8{g)@I=o%a8f2;-'
    'K=(&<oLCm;RYln$aCMF3tCAkWOkcF>7H_q0Wo2j;FBZ%S$74kvY}tYYHIiN+$ct;#Ul-'
    '3*v}SuPXehQkLgv)t=Cg0d^!5gYdTwt(5r~VTsw$mYyV4?Noge!y=yta~rTe9=*XQ-)!}w^!DqfD*{YK-TGJY-?W&L3j``RnVyL-kKeAN~fCOE'
    'A|Rqd4TSO{2neV3Pom%Chk_w_zwkoxrl0OYPN9{|L8S2yhHp)TUZ1-+>6X#T(>Gqr9j&$otlD{DjcXjrG~ZAc9-'
    'W53ueHgKB9*K{BVBoAM)MYy?mWXp4Z3l=|!^f(^<AXQLui!EM^*z8v%3U~2PJtck`x3y+Z)&Pi_9d>lo*5!b};_u*t*YKBv3gFe+fl?L1_=T54'
    'HbqM36^Kt<U0l>kB{x7<-!T90<r~U<cDMP`gJT31^8Wr6ANckE09mQ}zy'
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
                if tile.get('fertilizer_available'):
                    value+=prices['FERTILIZER'];ops.append(['COLLECT_FERTILIZER'])
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
    orders=[['SELL',k,n] for k,n in stock.items() if k in PRODUCTS and n>0]
    if hour<2:
        need=max(0,hires-len(farm['hands']))
        orders += [['HIRE'] for _ in range(min(need,10-len(orders))) ]
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
        return plan(observation, hires=10, exponent=1.0, watering=True)
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
