; Script para Inno Setup
; Veja a documentação em https://jrsoftware.org/ishelp/

; --- Definições do Pré-processador ---
; As variáveis MyAppVersion, MyExeName e MyIconFile são passadas pelo build.bat
; Ex: /DMyAppVersion="1.5" /DMyExeName="run.exe" /DMyIconFile="static\favicon.ico"
#define MyAppName "CatalogoDePecas"

; --- Valores Padrão (para compilação manual/IDE) ---
; Se as variáveis não forem passadas pela linha de comando, use estes valores.
#ifndef MyAppVersion
  #define MyAppVersion "1.8.3"
#endif
#ifndef MyExeName
  #define MyExeName "CatalogoDePecas.exe"
#endif
#ifndef MyIconFile
  #define MyIconFile "static\\favicon.ico"
#endif
[Setup]
; Informações básicas da aplicação
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=Spec
AppPublisherURL=https://www.seusite.com.br
AppSupportURL=https://www.seusite.com.br
AppUpdatesURL=https://www.seusite.com.br

; Diretório de instalação padrão (em Arquivos de Programas)
; Diretório de instalação padrão alterado para a pasta do usuário
; Isso evita a necessidade de privilégios de administrador (UAC) e
; permite que o aplicativo grave no banco e uploads sem problemas.
DefaultDirName={userappdata}\CatalogoDePecas
; Nome da pasta no Menu Iniciar
DefaultGroupName=Catálogo de Peças
; Define o diretório base de onde os arquivos de origem serão lidos.
; O PyInstaller coloca a saída na pasta 'dist'.
SourceDir=dist

; Nome do arquivo do instalador gerado (ex: instalador_catalogo_pecas_1.0.exe)
OutputBaseFilename=instalador_{#MyAppName}_v{#MyAppVersion}

; Configurações de compressão e aparência
Compression=lzma
SolidCompression=yes
WizardStyle=modern
 
; Ícone do instalador desativado para evitar problemas de caminho em ambientes com acentuação
; (opcional: aponte para um .ico em caminho ASCII e reative esta linha)
; SetupIconFile="static\\favicon.ico"
UninstallDisplayIcon={app}\{#MyExeName}

; Requer privilégios de administrador para instalar em Arquivos de Programas
; Não requer privilégios de administrador — instalador copia o banco e uploads para {userappdata}
PrivilegesRequired=none


[Languages]
; Define o idioma do instalador
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"


[Tasks]
; Opção para o usuário criar um atalho na área de trabalho
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked


[Files]
; Copia TODOS os arquivos e subpastas da saída do PyInstaller para o diretório de instalação
; IMPORTANTE: Execute o PyInstaller antes de compilar este script!
; A origem do executável é relativa ao 'SourceDir' (pasta 'dist').
Source: "{#MyExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Banco de dados e imagens - copiados para a pasta do usuário ({userappdata})
; para permitir gravação sem UAC.
Source: "..\build\package\data\catalogo.db"; DestDir: "{userappdata}\{#MyAppName}"; Flags: ignoreversion skipifsourcedoesntexist; Check: not FileExists(ExpandConstant('{userappdata}\\{#MyAppName}\\catalogo.db'))
Source: "..\build\package\uploads\*"; DestDir: "{userappdata}\{#MyAppName}\uploads"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

[Icons]
; Atalho no Menu Iniciar
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyExeName}"; IconFilename: "{app}\{#MyExeName}"
; Atalho na Área de Trabalho (se a tarefa "desktopicon" for selecionada)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyExeName}"
; Atalho para desinstalação no Menu Iniciar
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"


[UninstallDelete]
; Esta seção é necessária para que o compilador reconheça as variáveis
; e funções do desinstalador usadas na seção [Code] abaixo.
; A entrada abaixo é apenas para garantir que a seção não seja ignorada.
; O desinstalador já remove o executável principal por padrão.
Type: files; Name: "{app}\{#MyExeName}"


[Run]
; Executa a aplicação ao final da instalação, se o usuário marcar a opção
Filename: "{app}\{#MyExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent


[Code]
var
  RemoveData: Boolean;
  UserSaidYes: Boolean; // Variável para rastrear a escolha do usuário (Sim/Não)

// --- Funções para a Caixa de Diálogo Personalizada ---

// Evento para o clique no botão "Sim"
procedure YesButtonClick(Sender: TObject);
var
  Form: TForm;
  CheckBox: TCheckBox;
begin
  Form := TForm(TComponent(Sender).Owner);
  // Encontra a caixa de seleção no formulário e armazena seu estado
  CheckBox := TCheckBox(Form.FindComponent('RemoveDataCheck'));
  if Assigned(CheckBox) then
  begin
    RemoveData := CheckBox.Checked;
  end;
  UserSaidYes := True;
  Form.Close; // Fecha o formulário
end;

// Evento para o clique no botão "Não"
procedure NoButtonClick(Sender: TObject);
var
  Form: TForm;
begin
  Form := TForm(TComponent(Sender).Owner);
  UserSaidYes := False;
  Form.Close; // Fecha o formulário
end;

// Esta função é chamada logo antes da janela de confirmação da desinstalação ser exibida.
function InitializeUninstallStep(): Boolean;
var
  ConfirmForm: TForm;
  ConfirmLabel: TLabel;
  RemoveDataCheckBox: TCheckBox;
  YesButton, NoButton: TButton;
  ConfirmMsg: String;
begin
  // Inicializa as variáveis globais.
  RemoveData := False;
  UserSaidYes := False;

  // Cria a mensagem de confirmação padrão.
  ConfirmMsg := FmtMessage(CustomMessage('ConfirmUninstall'), ['{#MyAppName}']);

  // Cria o formulário personalizado
  ConfirmForm := TForm.Create(nil);
  try
    ConfirmForm.Caption := 'Confirmar Desinstalação';
    ConfirmForm.ClientWidth := 400;
    ConfirmForm.ClientHeight := 140;
    ConfirmForm.Position := poScreenCenter;
    ConfirmForm.BorderStyle := bsDialog;

    ConfirmLabel := TLabel.Create(ConfirmForm);
    ConfirmLabel.Parent := ConfirmForm;
    ConfirmLabel.SetBounds(16, 16, 368, 40);
    ConfirmLabel.Caption := ConfirmMsg;

    RemoveDataCheckBox := TCheckBox.Create(ConfirmForm);
    RemoveDataCheckBox.Parent := ConfirmForm;
    RemoveDataCheckBox.Name := 'RemoveDataCheck';
    RemoveDataCheckBox.SetBounds(16, 60, 368, 17);
    RemoveDataCheckBox.Caption := 'Remover todos os dados do usuário (banco de dados, imagens, etc.)';

    YesButton := TButton.Create(ConfirmForm);
    YesButton.Parent := ConfirmForm;
    YesButton.SetBounds(230, 100, 75, 25);
    YesButton.Caption := 'Sim';    
    YesButton.OnClick := @YesButtonClick;

    NoButton := TButton.Create(ConfirmForm);
    NoButton.Parent := ConfirmForm;
    NoButton.SetBounds(310, 100, 75, 25);
    NoButton.Caption := 'Não';
    NoButton.OnClick := @NoButtonClick;

    // Mostra o formulário e aguarda o usuário interagir.
    ConfirmForm.ShowModal;

  finally
    ConfirmForm.Free;
  end;

  // Retorna True se o usuário clicou em "Sim", False caso contrário.
  Result := UserSaidYes;
end;

// Esta função é chamada em diferentes etapas da desinstalação.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataPath: string;
begin
  // Executa somente no final da desinstalação E se a variável 'RemoveData' for verdadeira.
  // A variável 'RemoveData' foi definida pela caixa de seleção na função InitializeUninstallStep.
  if (CurUninstallStep = usPostUninstall) and (RemoveData) then
  begin
    DataPath := ExpandConstant('{userappdata}\{#MyAppName}');
    if DirExists(DataPath) then
      DelTree(DataPath, True, True, True);
  end;
end;