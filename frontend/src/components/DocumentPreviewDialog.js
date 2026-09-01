import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ExternalLink } from "lucide-react";

export default function DocumentPreviewDialog({ open, url, title = "Просмотр документа", onClose }) {
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent
        className="max-w-5xl w-[95vw] max-h-[92vh] rounded-none p-0 overflow-hidden"
        data-testid="document-preview-dialog"
      >
        <DialogHeader className="px-6 pt-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <DialogTitle className="font-heading text-2xl tracking-tight">{title}</DialogTitle>
              <DialogDescription>Предпросмотр готового договора в формате PDF.</DialogDescription>
            </div>
            {url && (
              <Button
                variant="outline"
                size="sm"
                className="rounded-none mr-8 shrink-0"
                onClick={() => window.open(url, "_blank")}
                data-testid="preview-open-tab-btn"
              >
                <ExternalLink className="h-4 w-4" />
                В новой вкладке
              </Button>
            )}
          </div>
        </DialogHeader>
        <div className="px-6 pb-6">
          {url ? (
            <object data={url} type="application/pdf" className="w-full h-[75vh] border border-border" data-testid="preview-iframe">
              <iframe title="preview" src={url} className="w-full h-[75vh] border border-border" />
            </object>
          ) : null}
        </div>
      </DialogContent>
    </Dialog>
  );
}
