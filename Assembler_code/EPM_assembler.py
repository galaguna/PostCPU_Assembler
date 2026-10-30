##########################################################################################
# Programa ensamblador para el microprocesador MPM (Máquina de Post Mejorada)
# Assembler program for the EPM (Enhanced Post Machine) microprocessor
##########################################################################################
# Universidad Autónoma Metropolitana, Unidad Lerma
# Programador: Gerardo Laguna
# 28 octubre de 2026
##########################################################################################
import os
import sys
import ply.lex as lex

#Diccionario de palabras reservadas
palabras_reservadas = {
    'org': 'ORIGEN',
    'nop': 'OP_NOP',
    'incdp' : 'OP_INCDP',
    'decdp' : 'OP_DECDP',
    'set' : 'OP_SET',
    'clr' : 'OP_CLR',
    'jmp'  : 'OP_JMP',
    'jz' : 'OP_JZ',
    'stop' : 'OP_STOP'
}
#Lista de tokens:
tokens=('TERMINADOR',
        'ETIQUETA',
        'DECIMAL',
        'HEXADECIMAL')+ tuple(palabras_reservadas.values())


##########################################################################################
#PLY (Python Lex-Yacc) evalua las reglas definidas como funciones en su orden de aparición
##########################################################################################

def t_TERMINADOR(t):
    r'[;\n\r]'  #El token 'TERMINADOR' puede ser ';', 'LF' o 'CR'

    if t.value in '\n\r': #Si el caracter es 'LF' o 'CR'
        t.lexer.lineno += 1 #Incrementa el contador de líneas del lexer.

    return t

def t_ETIQUETA(t):
    #Regla con expresión regular para token etiqueta
    #r'[a-zA-Z][a-zA-Z0-9_]*'
    #   - Inicia con letra (minúscula o mayúscula)
    #   - Termina una cadena compuesta por números y
    #     letras en el intervalo [A:F] (minúscula o mayúscula)
    #     incluyendo el guión bajo.
    r'[a-zA-Z][a-zA-Z0-9_]*'

    #Prevision para garantizar insensbilidad ante mayúsculas y minúsculas:
    lower_key=t.value.lower() #Valor (i.e. cadena) a minúsculas
    #Verificamos si la cadena del token es una palabra reservada:
    if lower_key in palabras_reservadas:
        t.type = palabras_reservadas[lower_key]

    return t

#Primero se define el token hexadecimal para capturar antes que nadie el prefijo '0x'
def t_HEXADECIMAL(t):
    #Regla con expresion regular para token hexadecimal
    #r'0[xX][0-9a-fA-F]+'
    #   - Inicia con 0
    #   - Le sigue x (minúscula o mayúscula)
    #   - Finalmente una cadena compuesta por números y
    #     letras en el intervalo [A:F] (minúscula o mayúscula)
    r'0[xX][0-9a-fA-F]+'
    t.value= int(t.value,16)
    return t

#Luego se define el token decimal que también puede comenzar con '0'
def t_DECIMAL(t):
    #Regla con expresión regular para token decimal
    r'\d+'
    t.value= int(t.value)
    return t

#Caracteres que se ignoran:
#espacio, tabulador, coma, punto, dos puntos.
t_ignore = ' \t,.:'

def t_error(t):
    print(f'Caracter ilegal:{t.value[0]} en línea {t.lineno}, columna {t.lexpos+1}')
    sys.exit()


#Construye el lexer
lexer = lex.lex()

##########################################################################################
#Variables globales:
##########################################################################################
Lista_codigo_maquina = []
block_org=0
block_org_ix=-1 #De entrada, un índice no válido, en espera de que se use almenos una primitiva ORG.
Tabla_etiquetas = {}
ProgramCounter = 0

# Diccionario de OP codes:
OP_code = {
    'OP_NOP': 0x00,
    'OP_INCDP': 0x01,
    'OP_DECDP': 0x02,
    'OP_SET': 0x03,
    'OP_CLR': 0x04,
    'OP_JMP': 0x05,
    'OP_JZ': 0x06,
    'OP_STOP': 0x07
}

#Lista de instrucciones que no requieren argumento:
OP_X_NOARG=(
    'OP_NOP',
    'OP_INCDP',
    'OP_DECDP',
    'OP_SET',
    'OP_CLR',
    'OP_STOP'
)

#Lista de instrucciones que requieren un argumento con la dirección destino:
OP_X_ADD=(
    'OP_JMP',
    'OP_JZ'
)

##########################################################################################
#Análisis léxico-sintáctico
##########################################################################################

def next_token():
    ntok = lexer.token()
    #Depuracion:
    #print(ntok)  # Imprime tipo (type), valor (value) del token, línea y columna.
    return ntok

def syntax_ana_ETIQUETA(lab):
    if lab.value not in Tabla_etiquetas:
        Tabla_etiquetas[lab.value] = ProgramCounter
    else:
        print(f'¡¡¡Error en línea {lab.lineno}, columna {lab.lexpos+1}: Etiqueta definida previamente!!!\n')
        sys.exit()

def syntax_ana_4ORIGEN():
    global ProgramCounter, block_org, block_org_ix
    tok = next_token()
    if tok.type == 'DECIMAL' or tok.type == 'HEXADECIMAL':
        block_size= ProgramCounter - block_org
        if block_org_ix >= 0: #Si ya se empleo la primitica ORG
            Lista_codigo_maquina[block_org_ix] = Lista_codigo_maquina[block_org_ix] + ' (SIZE ' + str(block_size) + ')'
        ProgramCounter = tok.value
        block_org=ProgramCounter
        block_org_ix=len(Lista_codigo_maquina)
        Lista_codigo_maquina.append('ORG 0x' + '{:04X}'.format(tok.value))

    else:
        print(f'¡¡¡Error de sintaxis en línea {tok.lineno}, columna {tok.lexpos+1}: Primitiva ORG sin argumento válido!!!\n')
        sys.exit()

def ensambla_OP_X_NOARG(op_key):
    global ProgramCounter
    Lista_codigo_maquina.append('0x'+'{:01X}'.format(OP_code[op_key]))
    ProgramCounter+=1

def ensambla_OP_X_ADD(op_key):
    global ProgramCounter
    tok = next_token()
    if tok.type == 'ETIQUETA' or tok.type == 'DECIMAL' or tok.type == 'HEXADECIMAL':
        Lista_codigo_maquina.append('0x' + '{:01X}'.format(OP_code[op_key]))
        ProgramCounter += 1
        if tok.type == 'ETIQUETA':
            Lista_codigo_maquina.append(tok.value)
            ProgramCounter += 1
            Lista_codigo_maquina.append(tok.value)
            ProgramCounter += 1
        else: #El argumento de dirección destino se specifica numericamente:
            ADDH= (tok.value >> 4)& 0xF
            Lista_codigo_maquina.append('0x' + '{:01X}'.format(ADDH))
            ProgramCounter += 1
            ADDL=tok.value & 0xF
            Lista_codigo_maquina.append('0x' + '{:01X}'.format(ADDL))
            ProgramCounter += 1
    else:
        print(f'¡¡¡Error de sintaxis en línea {tok.lineno}, columna {tok.lexpos+1}: Falta argumento destino válido (etiqueta o direccion)!!!\n')
        sys.exit()


def syntax_ana_INSTRUCCION(tok):
    if not(not tok or tok.type == 'TERMINADOR'):
        if tok.type in OP_X_NOARG:
            ensambla_OP_X_NOARG(tok.type)
        elif tok.type in OP_X_ADD:
            ensambla_OP_X_ADD(tok.type)
        else:
            print(f'¡¡¡Error de sintaxis en línea {tok.lineno}, columna {tok.lexpos+1}: Instrucción ASM desconocida!!!\n')
            sys.exit()

def default_ORIGEN():
    global ProgramCounter, block_org, block_org_ix
    block_org=ProgramCounter
    block_org_ix=len(Lista_codigo_maquina)
    Lista_codigo_maquina.append('ORG 0x' + '{:04X}'.format(block_org))

def analiza_linea_asm():
    tok = next_token()
    if not(not tok or tok.type == 'TERMINADOR'):
        if tok.type == 'ORIGEN':
            syntax_ana_4ORIGEN()
        else:
            if len(Lista_codigo_maquina) == 0:
                default_ORIGEN()

            if tok.type == 'ETIQUETA':
                syntax_ana_ETIQUETA(tok)
                tok = next_token()
                syntax_ana_INSTRUCCION(tok)
            else:
                syntax_ana_INSTRUCCION(tok)

def link_labels():
    N=len(Lista_codigo_maquina)

    for n in range(N):
        lexer.input(Lista_codigo_maquina[n])
        tok = next_token()
        if tok.type == 'ETIQUETA':
            if tok.value in Tabla_etiquetas:
                ADD=Tabla_etiquetas[tok.value]
                ADDH = (ADD >> 4) & 0xF
                ADDL = ADD & 0xF
                Lista_codigo_maquina[n]='0x' + '{:01X}'.format(ADDH)
                Lista_codigo_maquina[n+1]='0x' + '{:01X}'.format(ADDL)

            else:
                print(f'¡¡¡Error!!!: Etiqueta {tok.value} no definida!!!\n')
                sys.exit()

def close_code_block():
    block_size = ProgramCounter - block_org
    if block_org_ix >= 0:  # Si ya se empleó la primitiva ORG
        Lista_codigo_maquina[block_org_ix] = Lista_codigo_maquina[block_org_ix] + ' (SIZE ' + str(block_size) + ')'


#Uso de token() en forma manual, para ensamblar, línea por línea, un código fuente en texto:
def EPM_asm2hex(asm_file):
#asm_file: nombre del archivo con el código fuente en ensamblador, preferentemente con extensión asm
#Salida:
#Archivo con el código máquina (en formato texto), con el mismo nombre base que el archivo fuente, pero con extensión hex.
    try:
        with open(asm_file, 'r') as codigo:
            lexer.lineno =1 #Iniializamos contador de líneas del lexer
            #Iteramos línea por línea:
            for n_linea, linea in enumerate(codigo, start=1):
                lexer.lineno = n_linea #Número de línea en turno
                lexer.input (linea)
                #Depuracion:
                #print(f'Linea {n_linea}')
                #print(linea)
                analiza_linea_asm()

            close_code_block()
            #Depuracion:
            #print(Tabla_etiquetas)
            #print(ProgramCounter)
            #print(Lista_codigo_maquina)
            link_labels()
            print(Lista_codigo_maquina)
            # Guardar los resultados en un nuevo archivo de texto
            nombre_base, _ = os.path.splitext(asm_file)
            output_file = nombre_base + ".hex"
            with open(output_file, "w") as salida:
                salida.write("\n".join(Lista_codigo_maquina))
                print(f'Código máquina ensamblado en el archivo de salida {output_file} \n')

    except FileNotFoundError:
        print(f'El archivo {asm_file} no existe \n')


if __name__ == "__main__":

    EPM_asm2hex('Post_code.asm')