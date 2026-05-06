# Guía de Git para Agentes

## Estado del Repositorio

- **Remoto**: https://github.com/martingomezpizarro/Trabajo-Final-
- **Rama principal**: master
- **Usuario**: Martin

## Comandos常用

### Ver estado
```powershell
git status
```

### Hacer commit
```powershell
git add .
git commit -m "mensaje descriptivo"
```

### Subir cambios (push)
```powershell
git push
```

### Traer cambios (pull)
```powershell
git pull
```

### Ver diferencias
```powershell
git diff
git diff --staged
```

## Flujo de Trabajo Recomendado

1. Antes de hacer cambios: `git pull` (para tener la última versión)
2. Después de hacer cambios: `git add .` + `git commit -m "mensaje"` + `git push`

## Notas

- Todos los archivos ya están en el repositorio
- El `.gitignore` está configurado
- Hay archivos grandes en `data/basesingade deuda/` (>50MB) que pueden generar advertencias